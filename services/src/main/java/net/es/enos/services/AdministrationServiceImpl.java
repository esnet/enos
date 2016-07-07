/*
 * ESnet Network Operating System (ENOS) Copyright (c) 2016, The Regents
 * of the University of California, through Lawrence Berkeley National
 * Laboratory (subject to receipt of any required approvals from the
 * U.S. Dept. of Energy).  All rights reserved.
 *
 * If you have questions about your rights to use or distribute this
 * software, please contact Berkeley Lab's Innovation & Partnerships
 * Office at IPO@lbl.gov.
 *
 * NOTICE.  This Software was developed under funding from the
 * U.S. Department of Energy and the U.S. Government consequently retains
 * certain rights. As such, the U.S. Government has been granted for
 * itself and others acting on its behalf a paid-up, nonexclusive,
 * irrevocable, worldwide license in the Software to reproduce,
 * distribute copies to the public, prepare derivative works, and perform
 * publicly and display publicly, and to permit other to do so.
 *
 */
package net.es.enos.services;

import com.google.common.base.Strings;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;
import io.swagger.annotations.Contact;
import io.swagger.annotations.Info;
import io.swagger.annotations.License;
import io.swagger.annotations.SwaggerDefinition;
import java.net.URI;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.PathParam;
import javax.ws.rs.Produces;
import javax.ws.rs.WebApplicationException;
import javax.ws.rs.core.Context;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;
import javax.ws.rs.core.UriBuilder;
import javax.ws.rs.core.UriInfo;
import net.es.enos.services.gson.JsonProxy;
import net.es.netshell.services.BundleVersionResource;
import net.es.netshell.services.BundleVersionService;
import org.osgi.framework.BundleContext;
import org.osgi.framework.InvalidSyntaxException;
import org.osgi.framework.ServiceReference;
import org.osgi.service.component.annotations.Activate;
import org.osgi.service.component.annotations.Component;
import org.osgi.service.component.annotations.Deactivate;
import org.osgi.service.component.annotations.Modified;
import org.osgi.service.component.annotations.Reference;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * The ENOS administration web service.
 *
 * Used JAX-RS to define a RESTful API and SCR to define this class as an
 * OSGi service.
 */

/*
 * Due to a bug in the jax-rs-provider-swagger bundle the default swagger configuration
 *  files does not get references properly.  Using this annotation, while verbose, will
 * achieve the desired result until a fix is available.
 */
@SwaggerDefinition(
    basePath = "/services",
    info = @Info(
    description = "This API provides access to programmable ENOS features.",
    version = "1.0",
    title = "ENOS Services API",
    termsOfService = "ESnet Network Operating System (ENOS) Copyright (c) 2016, The Regents of the University of California, through Lawrence Berkeley National Laboratory (subject to receipt of any required approvals from the U.S. Dept. of Energy).  All rights reserved.",
    contact = @Contact(name = "ENOS Development Team", email = "enos@es.net", url = "https://github.com/esnet/enos"),
    license = @License(name = "Lawrence Berkeley National Labs BSD variant license", url = "https://spdx.org/licenses/BSD-3-Clause-LBNL.html"))
)

@Path("/admin/v1")
@Api(value = "administration")
@Component(enabled = true, immediate = false, service = AdministrationService.class,
        configurationPid = Configuration.PID)
public class AdministrationServiceImpl implements AdministrationService {
    private final Logger logger = LoggerFactory.getLogger(getClass());

    private BundleContext bundleContext;
    private JsonProxy proxy;
    private String uriTransform;

    /**
     * This method is called when the service is activated by the OSGi framework.
     *
     * @param bundleContext The OSGi bundle context providing access to the OSGi service registry.
     * @param config The configuration information for this service.
     */
    @Activate
    public void activate(BundleContext bundleContext, Map<String,Object> config) {
        this.bundleContext = bundleContext;
        uriTransform = (String) config.get(Configuration.KEY_URITRANSFORM);
        logger.info("enos administration service started, uriTransform=" + uriTransform);
    }

    /**
     * This method is called when the service is deactivated by the OSGi framework.
     *
     * @param bundleContext The OSGi bundle context providing access to the OSGi service registry.
     * @param config The configuration information for this service.
     */
    @Deactivate
    public void deactivate(BundleContext bundleContext, Map<String,Object> config) {
        // We need to unregister any services and listeners.
        logger.info("enos administration service stopped");
    }

    /**
     * This method is called when a change to the service configuration is detected.
     *
     * @param config The configuration information for this service.
     */
    @Modified
    void modified(Map<String,Object> config) {
        logger.info("Modifying service configuration: " + Configuration.PID);
        uriTransform = (String) config.get(Configuration.KEY_URITRANSFORM);
        logger.info("Modified uriTransform=" + uriTransform);
    }

    /**
     * Injects a reference to the JSON proxy service used for serialization
     * of Java objects into JSON.
     *
     * @param proxy The reference to the JSON proxy.
     */
    @Reference
    void setJsonProxy(JsonProxy proxy) {
        this.proxy = proxy;
    }

    /**
     * Transform the incoming path using configured rules.
     *
     * @param uriInfo
     * @return UriBuilder containing the transformed path.
     */
    private UriBuilder getPath(UriInfo uriInfo) {
        if (Strings.isNullOrEmpty(uriTransform)) {
            return uriInfo.getAbsolutePathBuilder();
        }

        // We want to manipulate the URL using string matching.
        String url = uriInfo.getAbsolutePath().toASCIIString().trim();
        String fromURI = Configuration.getFromURI(uriTransform);
        String toURI = Configuration.getToURI(uriTransform);

        // Remove the URI prefix if one was provided.
        if (!Strings.isNullOrEmpty(fromURI)) {
            if (!url.startsWith(fromURI)) {
                // We do not have a matching URI prefix so return full URL.
                return uriInfo.getAbsolutePathBuilder();
            }

            url = url.replaceFirst(fromURI, "");
        }

        // Add the URI prefix if one was provided.
        if (!Strings.isNullOrEmpty(toURI)) {
            url = toURI + url;
        }

        return UriBuilder.fromUri(url);
    }

    /**
     * Returns a list of ENOS/Netshell bundles activated within the server instance.
     *
     * @param uriInfo The incoming URI context used to invoke the service.
     * @return A RESTful response.
     */
    @ApiOperation(
        value = "Get a detailed list of deployed ENOS bundle versions.",
        notes = "Returns a complete list of installed ENOS modules and the detailed version information.",
        response = BundleVersionResource.class,
        responseContainer = "List")
    @ApiResponses(
        value = {
            @ApiResponse(code = 200, message = "OK - Success", response=BundleVersionResource.class),
            @ApiResponse(code = 500, message = "INTERNAL_SERVER_ERROR - Could not get OSGI service references for BundleVersionService", response=Error.class),
        }
    )
    @GET
    @Produces(MediaType.APPLICATION_JSON)
    @Path("/versions")
    @Override
    public Response getVersions(@Context UriInfo uriInfo) {
        List<BundleVersionResource> versions = new ArrayList<>();
        try {
            Collection<ServiceReference<BundleVersionService>> serviceReferences = bundleContext.getServiceReferences(BundleVersionService.class, null);
            for (ServiceReference<BundleVersionService> serviceRef : serviceReferences) {
                BundleVersionService service = bundleContext.getService(serviceRef);
                BundleVersionResource version = service.getVersion();
                URI uri = getPath(uriInfo).path(version.getId()).build();
                version.setHref(uri.toASCIIString());
                versions.add(version);
            }
        } catch (InvalidSyntaxException ex) {
            // Internal server error.
            logger.error("Could not get OSGI service references", ex);
            throw new WebApplicationException(Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                .entity(proxy.serialize(
                    new Error.Builder()
                            .withError("internal_error")
                            .withErrorDescription("Could not get OSGI service references for BundleVersionService")
                            .build()
                )).build());
        }

        return Response.ok().entity(proxy.serializeList(versions, BundleVersionResource.class)).build();
    }

    /**
     * Returns the Github/bundle details for a specific bundle.
     *
     * @param id Identifier of the target bundle.
     * @param uriInfo The incoming URI context used to invoke the service.
     * @return A RESTful response.
     */
    @GET
    @Produces(MediaType.APPLICATION_JSON)
    @ApiOperation(
        value = "Get a specific deployed ENOS bundle version.",
        notes = "Returns information about the requested ENOS bundle including detailed version information.",
        response = BundleVersionResource.class)
    @ApiResponses(
        value = {
            @ApiResponse(code = 200, message = "OK - Success", response=BundleVersionResource.class),
            @ApiResponse(code = 404, message = "NOT_FOUND - Bundle identifier not found", response=Error.class),
            @ApiResponse(code = 500, message = "INTERNAL_SERVER_ERROR - Could not get OSGI service references for BundleVersionService", response=Error.class),
        }
    )
    @Path("/versions/{id}")
    @Override
    public Response getVersion(@ApiParam(value = "Bundle identifier", required = true) @PathParam("id") String id, @Context UriInfo uriInfo) {
        try {
            Collection<ServiceReference<BundleVersionService>> serviceReferences = bundleContext.getServiceReferences(BundleVersionService.class, null);
            for (ServiceReference<BundleVersionService> serviceRef : serviceReferences) {
                BundleVersionService service = bundleContext.getService(serviceRef);
                BundleVersionResource version = service.getVersion();
                if (version.getId().equalsIgnoreCase(id)) {
                    version.setHref(getPath(uriInfo).build().toASCIIString());
                    return Response.ok().entity(proxy.serialize(version)).build();
                }
            }
        } catch (InvalidSyntaxException ex) {
            // Internal server error.
            logger.error("Could not get OSGI service references", ex);
            throw new WebApplicationException(Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                .entity(proxy.serialize(
                    new Error.Builder()
                            .withError("internal_error")
                            .withErrorDescription("Could not get OSGI service references for BundleVersionService")
                            .build()
                )).build());
        }

        // 404 - not found.
        throw new WebApplicationException(Response.status(Response.Status.NOT_FOUND)
            .entity(proxy.serialize(
                    new Error.Builder()
                            .withError("not_found")
                            .withErrorDescription("Could not find OSGI service reference for bundle ID=" + id)
                            .build()
            )).build());
    }
}

