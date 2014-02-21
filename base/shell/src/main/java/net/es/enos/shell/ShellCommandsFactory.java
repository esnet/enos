package net.es.enos.shell;

import net.net.es.enos.shell.annotations.ShellCommand;

import java.lang.reflect.Method;
import java.util.HashMap;

/**
 * Created by lomax on 2/21/14.
 */
public class ShellCommandsFactory {

    private static HashMap<String, Method> shellCommands = new HashMap<String, Method>();

    public static void registerShellModule (Class shellModule) {
        Method[] methods = shellModule.getMethods();

        for (Method method : methods) {
            ShellCommand command = method.getAnnotation(ShellCommand.class);
            if (command != null) {
                // This method is command.
                System.out.println("Adding " + command.name());
                ShellCommandsFactory.shellCommands.put(command.name(),method);
            }
        }
    }

    public static Method getCommandMethod (String command) {
        return ShellCommandsFactory.shellCommands.get(command);
    }
}
