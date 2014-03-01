package net.es.enos.shell;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Path;
import java.nio.file.Paths;


import jline.UnixTerminal;
import jline.console.completer.StringsCompleter;
import net.es.enos.kernel.exec.KernelThread;


import jline.console.ConsoleReader;
import net.es.enos.shell.annotations.ShellCommand;

public class Shell implements Runnable {

    private InputStream in = null;
    private OutputStream out = null;
    private ConsoleReader consoleReader = null;
    private StringsCompleter stringsCompleter = null;
    private KernelThread kernelThread = null;
    private String prompt = "\nenos";

    public static String banner =
            " _       __     __                             __           _______   ______  _____\n" +
            "| |     / /__  / /________  ____ ___  ___     / /_____     / ____/ | / / __ \\/ ___/\n" +
            "| | /| / / _ \\/ / ___/ __ \\/ __ `__ \\/ _ \\   / __/ __ \\   / __/ /  |/ / / / /\\__ \\ \n" +
            "| |/ |/ /  __/ / /__/ /_/ / / / / / /  __/  / /_/ /_/ /  / /___/ /|  / /_/ /___/ / \n" +
            "|__/|__/\\___/_/\\___/\\____/_/ /_/ /_/\\___/   \\__/\\____/  /_____/_/ |_/\\____//____/  \n" +
            "                                                                                                                                                                                                               ";

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

    public String getPrompt() {
        return prompt;
    }

    public void setPrompt(String prompt) {
        this.prompt = "\n" + prompt;
    }

    public void run() {

        this.kernelThread = KernelThread.getCurrentKernelThread();

        System.out.println ("Shell Starting");

        this.setPrompt(kernelThread.getUser().getName() + "@enos> ");

        this.out = new ShellOutputStream(out);
        try {
            this.out.write(Shell.banner.getBytes());
            this.out.flush();
        } catch (IOException e) {
            e.printStackTrace();
        }
        ;
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
                String line = this.consoleReader.readLine(this.prompt);
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
                } catch (Exception e) {
                    // This is a catch all. Make sure that the thread recovers in a correct state
                    this.print( e.toString());
                    this.fixThread();
                }
            } catch (IOException e) {;
                break;
            }
        }
    }

    private void fixThread() {

    }
}
