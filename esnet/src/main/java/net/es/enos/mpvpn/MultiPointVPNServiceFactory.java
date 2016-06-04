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
    private PyObject pyObject;
    private String pythonPath;

    /**
     * Create a new PythonInterpreter object, then use it to
     * execute some python code. In this case, we want to
     * import the python module that we will coerce.
     * <p>
     * Once the module is imported than we obtain a reference to
     * it and assign the reference to a Java variable
     */

    public MultiPointVPNServiceFactory() {
        PythonInterpreter interpreter = new PythonInterpreter();
        interpreter.exec("from layer2.vpn.vpn import VPNService");
        this.pyObject = interpreter.get("VPNService");
    }

    /**
     * The create method is responsible for performing the actual
     * coercion of the referenced python module into Java bytecode
     */

    public MultiPointVPNService create(String pythonPath) {
        PyObject obj = this.pyObject.__call__();
        return (MultiPointVPNService) obj.__tojava__(MultiPointVPNService.class);
    }
}
