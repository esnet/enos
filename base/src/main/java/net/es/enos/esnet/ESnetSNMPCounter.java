package net.es.enos.esnet;

import net.sf.json.JSONArray;
import org.codehaus.jackson.annotate.JsonIgnore;

import java.util.ArrayList;
import java.util.List;

/**
 * Created by lomax on 7/10/14.
 */
public class ESnetSNMPCounter {

    private String end_time;
    private String begin_time;
    private String cf;
    private List<JSONArray> data;

    private String agg;

    public String getAgg() {
        return agg;
    }

    public void setAgg(String agg) {
        this.agg = agg;
    }

    public String getEnd_time() {
        return end_time;
    }

    public void setEnd_time(String end_time) {
        this.end_time = end_time;
    }

    public String getBegin_time() {
        return begin_time;
    }

    public void setBegin_time(String begin_time) {
        this.begin_time = begin_time;
    }

    public String getCf() {
        return cf;
    }

    public void setCf(String cf) {
        this.cf = cf;
    }

    public List<JSONArray> getData() {
        return data;
    }

    public void setData(List<JSONArray> data) {
        this.data = data;
    }

    @JsonIgnore
    public List<ESnetSNMPData> getTimeSerie() {

        ArrayList<ESnetSNMPData> timeSerie = new ArrayList<ESnetSNMPData>();

        for (JSONArray jsonData : this.data) {
            ESnetSNMPData d = new ESnetSNMPData(jsonData.getString(0), jsonData.getString(1));
            timeSerie.add(d);
        }
        return timeSerie;
    }
}
