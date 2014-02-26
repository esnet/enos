package net.es.enos.python;

import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.shell.ShellInputStream;
import net.es.enos.shell.annotations.ShellCommand;


import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.util.Arrays;

import org.python.util.InteractiveInterpreter;
import org.python.util.InteractiveConsole;
// import org.python.util.JLineConsole;

import javax.print.DocFlavor;

/**
 * Created by lomax on 2/20/14.
 */
public class PythonShell {

    @ShellCommand(
            name="python",
            forwardLines=false
    )
    public static void startPython (String[] args, InputStream in, OutputStream out, OutputStream err) {
        System.out.println ("Starting Python");

        try {
            InteractiveConsole console = new InteractiveConsole();

            console.setOut(out);
            console.setErr(err);
            console.setIn(in);
            // Start the interactive session
            console.interact();
        } catch (Exception e) {
            e.printStackTrace();
            Thread.dumpStack();
        }

        System.out.println ("Exits Python");
    }

    @ShellCommand(
            name="test"
    )
    public static void test(String[] args, InputStream in, OutputStream out, OutputStream err) {
        try {
            out.write("Hello World\n".getBytes());
            for (int i=1; i < args.length; ++i) {
                String line = "argument " + i + "= " + args[i] + "\n";
                out.write(line.getBytes());
            }
            out.flush();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
