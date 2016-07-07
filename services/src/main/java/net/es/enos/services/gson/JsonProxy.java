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
package net.es.enos.services.gson;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonDeserializationContext;
import com.google.gson.JsonDeserializer;
import com.google.gson.JsonElement;
import com.google.gson.JsonParseException;
import com.google.gson.JsonPrimitive;
import com.google.gson.JsonSerializationContext;
import com.google.gson.JsonSerializer;
import java.lang.reflect.ParameterizedType;
import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import javax.ws.rs.core.GenericType;
import javax.ws.rs.core.Response;
import javax.xml.datatype.DatatypeConfigurationException;
import javax.xml.datatype.DatatypeFactory;
import javax.xml.datatype.XMLGregorianCalendar;
import org.glassfish.jersey.client.ChunkedInput;
import org.osgi.framework.BundleContext;
import org.osgi.service.component.annotations.Activate;
import org.osgi.service.component.annotations.Component;
import org.osgi.service.component.annotations.Deactivate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 *
 * @author hacksaw
 */
@Component(enabled = true, immediate = true, service = JsonProxy.class)
public class JsonProxy {
    private final Logger logger = LoggerFactory.getLogger(getClass());
    private final Gson serializer;

    @Activate
    public void activate(BundleContext bc, Map<String,Object> config) throws Exception {
        logger.info("JsonProxy service started");
    }

    @Deactivate
    void deactivate(BundleContext bc, Map<String,Object> config) {
        logger.info("JsonProxy service stopped");
    }

    public JsonProxy() {
        GsonBuilder gson = new GsonBuilder();
        gson.registerTypeAdapter(XMLGregorianCalendar.class, new XMLGregorianCalendarSerializer());
        gson.registerTypeAdapter(XMLGregorianCalendar.class, new XMLGregorianCalendarDeserializer());
        gson.setExclusionStrategies(new JsonExclusionStrategy());
        serializer = gson.create();
    }

    public String serialize(Object obj) {
        return serializer.toJson(obj);
    }

    public <T extends Object> T deserialize(String json, Class<T> classOfT) {
        return serializer.fromJson(json, classOfT);
    }

    public <T extends Object> T deserialize(Response response, Class<T> classOfT) {
        final ChunkedInput<String> chunkedInput = response.readEntity(new GenericType<ChunkedInput<String>>() {});
        String chunk;
        StringBuilder buffer = new StringBuilder();
        while ((chunk = chunkedInput.read()) != null) {
            buffer.append(chunk);
        }
        response.close();
        return serializer.fromJson(buffer.toString(), classOfT);
    }

    public <T extends Object> String serializeList(Object obj, Class<T> classOfT) {
        Type type = new ListParameterizedType(classOfT);
        return serializer.toJson(obj, type);
    }

    public <T extends Object> List<T> deserializeList(String json, Class<T> classOfT) {
        Type type = new ListParameterizedType(classOfT);
        return serializer.fromJson(json, type);
    }

    public <T extends Object> List<T> deserializeList(Response response, Class<T> classOfT) {
        final ChunkedInput<String> chunkedInput = response.readEntity(new GenericType<ChunkedInput<String>>() {});
        String chunk;
        StringBuilder buffer = new StringBuilder();
        while ((chunk = chunkedInput.read()) != null) {
            buffer.append(chunk);
        }
        response.close();
        return deserializeList(buffer.toString(), classOfT);
    }

    private static class ListParameterizedType implements ParameterizedType {

        private final Type type;

        private ListParameterizedType(Type type) {
            this.type = type;
        }

        @Override
        public Type[] getActualTypeArguments() {
            return new Type[] {type};
        }

        @Override
        public Type getRawType() {
            return ArrayList.class;
        }

        @Override
        public Type getOwnerType() {
            return null;
        }

        @Override
        public int hashCode() {
            int hash = 3;
            hash = 83 * hash + Objects.hashCode(this.type);
            return hash;
        }

        @Override
        public boolean equals(Object other) {
            if (this == other) return true;
            if (other == null) return false;
            if (this.getClass() != other.getClass()) return false;
            ListParameterizedType otherType = (ListParameterizedType) other;
            return (this.type == otherType.type);
        }
    }

    private class XMLGregorianCalendarSerializer implements JsonSerializer<XMLGregorianCalendar> {
        @Override
        public JsonElement serialize(XMLGregorianCalendar src, Type typeOfSrc, JsonSerializationContext context) {
            return new JsonPrimitive(src.toString());
        }
    }

    private class XMLGregorianCalendarDeserializer implements JsonDeserializer<XMLGregorianCalendar> {
      @Override
      public XMLGregorianCalendar deserialize(JsonElement json, Type typeOfT, JsonDeserializationContext context)
          throws JsonParseException {
          try {
              return DatatypeFactory.newInstance().newXMLGregorianCalendar(json.getAsJsonPrimitive().getAsString());
          } catch (DatatypeConfigurationException ex) {
              logger.error("XMLGregorianCalendarDeserializer: Could not convert supplied date " +  json.getAsJsonPrimitive().getAsString());
              return(null);
          }
      }
    }
}
