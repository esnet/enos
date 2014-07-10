package net.es.enos.esnet;

/**
 * Created by lomax on 7/10/14.
 */
public class ESnetSNMPInterfaceStats {

    private boolean leaf;
    private String uri;
    private String name;

    public boolean isLeaf() {
        return leaf;
    }

    public void setLeaf(boolean leaf) {
        this.leaf = leaf;
    }

    public String getUri() {
        return uri;
    }

    public void setUri(String uri) {
        this.uri = uri;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

}
