package net.es.enos.boot;

import net.es.enos.python.PythonShell;
import net.es.enos.shell.ShellCommandsFactory;
import net.es.enos.sshd.SShd;
import net.es.enos.shell.Shell;
import net.es.enos.sshd.ShellFactory;

import java.io.IOException;

/**
 * Created by lomax on 2/20/14.
 */
public class BootStrap {
    private static BootStrap bootStrap = null;
    private String[] args = null;
    private SShd sshd = null;


    public Shell getShell() {
        return shell;
    }

    private Shell shell = null;

    public SShd getSshd() {
        return sshd;
    }

    public String[] getArgs() {
        return args;
    }

    public static void main(String[] args) {
        BootStrap myBbootStrap= new BootStrap(args);
        myBbootStrap.startServices();

        myBbootStrap.postInitialization();

        System.out.println("Bootstrap thread exits");
    }

    private BootStrap (String[] args) {
        this.args = args;
    }



    public static BootStrap getBootStrap() {
        return BootStrap.bootStrap;
    }

    public void startServices() {
        this.sshd = SShd.getSshd();
        try {
            this.sshd.start();
        } catch (IOException e) {
            e.printStackTrace();
        }
        // Add Shell Modules
        addShellModules();
    }

    private void addShellModules() {
        ShellCommandsFactory.registerShellModule(PythonShell.class);
    }
    public void stop() {
        synchronized (this) {
            notify();
        }
    }
    private void postInitialization() {
        synchronized (this) {
            try {
                wait();
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }
}
