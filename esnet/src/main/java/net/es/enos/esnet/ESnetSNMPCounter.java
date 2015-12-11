/*
 * ESnet Network Operating System (ENOS) Copyright (c) 2015, The Regents
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
 */
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
