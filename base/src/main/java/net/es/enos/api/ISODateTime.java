package net.es.enos.api;

import org.joda.time.DateTime;

/**
 * Created by lomax on 5/28/14.
 */
public class ISODateTime  {
    private String isoDateTime;
    private DateTime dateTime;

    public ISODateTime() {

    }

    public ISODateTime(String utc) {
        // This DateTime constructor takes a local timestamp not an UTC. Timestamps are in milliseconds
        this.dateTime = new DateTime(Long.parseLong(utc + "000"));
        this.isoDateTime = this.dateTime.toString();
    }

    public String getIsoDateTime() {
        return this.isoDateTime;
    }

    public void setIsoDateTime(String isoDateTime) {
        this.isoDateTime = isoDateTime;
        this.dateTime = DateTime.parse(isoDateTime);
    }

    public String toString() {
        return this.isoDateTime;
    }

    public DateTime toDateTime() {
        return this.dateTime;
    }
}
