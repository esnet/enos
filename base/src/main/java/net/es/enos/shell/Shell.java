package net.es.enos.shell;

import java.io.OutputStreamWriter;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Type;
import java.util.HashMap;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;


import jline.UnixTerminal;
import jline.console.completer.StringsCompleter;
import net.es.enos.kernel.exec.KernelThread;


import jline.console.ConsoleReader;
import net.es.enos.shell.annotations.ShellCommand;

public class Shell extends KernelThread {

    private InputStream in = null;
    private OutputStream out = null;
    private ConsoleReader consoleReader = null;
    private StringsCompleter stringsCompleter = null;

    public OutputStream getOut() {
        return out;
    }

    public void setOut(OutputStream out) {
        this.out = out;
    }

    public InputStream getIn() {
        return in;
    }

    public void setIn(InputStream in) {
        this.in = in;
    }

    public Shell(InputStream in, OutputStream out) throws IOException {
        super(in,out);
        this.in = in;
        this.out = out;

    }

    private void print(String line) {
        try {
            this.out.write(line.getBytes());
            this.out.flush();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public void run() {

        System.out.println ("Shell Starting");


        this.out = new ShellOutputStream(out);

        try {
                this.consoleReader = new ConsoleReader(this.in, this.out, new UnixTerminal());
        } catch (Exception e) {
            e.printStackTrace();
        }
        this.in = new ShellInputStream(this.in, this.consoleReader);
        // consoleReader.addCompleter(this.stringsCompleter);

        Method method = null;

        while (true) {
            try {
                String line = this.consoleReader.readLine("\nenos> ");
                if (line == null) {
                    continue;
                }

                String[] args = line.split(" ");
                method = ShellCommandsFactory.getCommandMethod(args[0]);
                if (method == null) {
                    // Non existing command
                    this.print(args[0] + " is an invalid command");
                    continue;
                }
                try {
                    ShellCommand command = method.getAnnotation(ShellCommand.class);
                    if (command.forwardLines()) {
                        method.invoke(null, args, this.in, this.out, this.out);
                    } else {
                        // Assume static method
                        method.invoke(null, args, this.in, this.out, this.out);
                    }
                } catch (IllegalAccessException e) {
                    this.print(e.toString());
                    continue;
                } catch (InvocationTargetException e) {
                   this.print( e.toString());
                   continue;
                }
            } catch (IOException e) {;
                break;
            }
        }
    }
}
