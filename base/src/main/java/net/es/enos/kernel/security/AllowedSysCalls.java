package net.es.enos.kernel.security;

/**
 * Created by lomax on 2/28/14.
 */

import com.sun.org.apache.bcel.internal.generic.ALOAD;
import net.es.enos.kernel.exec.KernelThread;

import java.util.LinkedList;
import java.util.List;

/**
 * List of classes that are allowed to change the privileged status of an
 * application thread.
 */
public final class AllowedSysCalls {
    static private List<Class> allowedSysCallClasses = new LinkedList<Class>();

    {
        allowedSysCallClasses.add(KernelThread.class);
    }

    public static List<Class> getAllowedClasses() {
        LinkedList<Class> ret = new LinkedList<Class>(AllowedSysCalls.allowedSysCallClasses);
        ret.add(KernelThread.class);
        return ret;
    }

    public static boolean isAllowed (Class c) {
        return AllowedSysCalls.allowedSysCallClasses.contains(c);
    }
}
