package net.es.enos.esnet;

/**
 * Created by lomax on 7/10/14.
 */
public class ESnetSNMPData {
    private String time;
    private float value;

    public ESnetSNMPData (String time, String value) {
        this.time = time;
        this.value = Float.parseFloat(value);
    }

    public String getTime() {
        return time;
    }

    public void setTime(String time) {
        this.time = time;
    }

    public float getValue() {
        return value;
    }

    public void setValue(float value) {
        this.value = value;
    }
}
