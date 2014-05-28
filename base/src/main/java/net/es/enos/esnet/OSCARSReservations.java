package net.es.enos.esnet;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/**
 * Created by lomax on 5/28/14.
 */
public class OSCARSReservations {

    /**
     * Returns the list of ACTIVE or RESERVED OSCARS circuits.
     * @return
     * @throws IOException
     */
    public static List<ESnetCircuit> retrieveScheduledCircuits() throws IOException {
        return new ESnetTopology().retrieveJSONTopology().getCircuits();
    }
}
