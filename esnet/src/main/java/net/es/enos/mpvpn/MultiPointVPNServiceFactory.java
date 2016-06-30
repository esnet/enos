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

package net.es.enos.mpvpn;

import org.python.core.PyObject;
import org.python.core.PyString;
import org.python.util.PythonInterpreter;

public class MultiPointVPNServiceFactory {

    static private  MultiPointVPNService vpnService = null;

    static public MultiPointVPNService getVpnService() {
        return vpnService;
    }

    /**
     * The create method is responsible for performing the actual
     * coercion of the referenced python module into Java bytecode
     */
    static public void create(String pythonPath) {
        if (vpnService != null) {
            throw new RuntimeException("MP-VPN Service has already been created.");
        }
        PythonInterpreter interpreter = new PythonInterpreter();
        if (pythonPath == null) {
            interpreter.exec("from layer2.vpn.vpn import VPNService");
        } else {
            interpreter.exec(pythonPath);
        }
        PyObject pyObject = interpreter.get("VPNService");
        PyObject obj = pyObject.__call__();
        vpnService = (MultiPointVPNService) obj.__tojava__(MultiPointVPNService.class);
    }

    static public void delete() {
        vpnService = null;
    }
}
