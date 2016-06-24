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
package net.es.enos.services.example;

import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;
import io.swagger.annotations.Contact;
import io.swagger.annotations.Info;
import io.swagger.annotations.License;
import io.swagger.annotations.SwaggerDefinition;
import javax.ws.rs.DefaultValue;
import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.QueryParam;
import javax.ws.rs.core.MediaType;

/**
 * A simple JAX-RS example service with swagger annotations.
 */

/* Due to a bug in the jax-rs-provider-swagger bundle the default swagger configuration
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

@Path("/hello")
@Api(value = "/hello")
public class ExampleService {
    private static final String salutation = "Hello";

    @GET
    @Produces(MediaType.APPLICATION_JSON)
    @ApiOperation(
        value = "Generate a greeting based on supplied name",
        notes = "Return a completed greeting in the response",
        response = ExampleResource.class,
        responseContainer = "List")
    @ApiResponses(
        value = {
            @ApiResponse(code = 200, message = "Success")
        }
    )
    public ExampleResource sayHello(
            @ApiParam(value = "Name for the greeting", required = false)
            @DefaultValue("world!") @QueryParam("name") String name) {
        ExampleResource rss = new ExampleResource();
        rss.setMessage(salutation + " " + name);
        return rss;
    }
}

