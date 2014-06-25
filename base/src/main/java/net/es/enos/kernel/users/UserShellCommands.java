/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.kernel.users;

import jline.console.ENOSConsoleReader;
import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.shell.ENOSTerminal;
import net.es.enos.shell.annotations.ShellCommand;

import java.io.*;
import java.nio.file.Paths;
import java.nio.file.Path;

import jline.UnixTerminal;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class UserShellCommands {
    @ShellCommand(name = "adduser",
    shortHelp = "Add a user to the system",
    longHelp = "Required arguments are a username, an initial password, a user class, a name, an organization name, and an email.\n" +
            "The user class should be either \"root\" or \"user\".",
    privNeeded = true)
    public static void addUser(String[] args, InputStream in, OutputStream out, OutputStream err) {
        Logger logger = LoggerFactory.getLogger(UserShellCommands.class);
        logger.info("adduser with {} arguments", args.length);

        boolean newUser = false;
        PrintStream o = new PrintStream(out);

        // Argument checking
        if (args.length != 7) {
            o.println("Usage:  adduser <username> <password> <userclass> <name> <organization> <email>");
            return;
        }

        UserProfile newProfile = new UserProfile(args[1], args[2], args[3], args[4], args[5], args[6]);

        newUser = Users.getUsers().createUser(newProfile);

        if (newUser) {
            o.print("New User created!");
        } else {
            o.print("Unable to create new user");
        }

    }

    @ShellCommand(name = "passwd",
            shortHelp = "Change user password",
            longHelp = "No arguments are required; this command will prompt for them interactively.\n")
    public static void passwd(String[] args, InputStream in, OutputStream out, OutputStream err) {
        Logger logger = LoggerFactory.getLogger(UserShellCommands.class);
        logger.info("passwd with {} arguments", args.length);

        PrintStream o = new PrintStream(out);

        ENOSConsoleReader consoleReader = null;
        try {
            consoleReader = new ENOSConsoleReader(in, out, new ENOSTerminal());
        } catch (Exception e) {
            e.printStackTrace();
            return;
        }
        // in = new ShellInputStream(in, consoleReader);

        try {
            // Get our current username.
            String thisUserName = KernelThread.getCurrentKernelThread().getUser().getName();

            // If this thread is privileged, then ask for a username (because we can set anybody's passwd).
            // If not privileged, require password verification to change our own passwd.
            String userName, oldPassword;
            if (KernelThread.getCurrentKernelThread().isPrivileged()) {
                userName = consoleReader.readLine("Username (default = " + thisUserName + "): ");
                if (userName.isEmpty()) {
                    userName = thisUserName;
                }
            }
            else {
                userName = KernelThread.getCurrentKernelThread().getUser().getName();
                oldPassword = consoleReader.readLine("Old password: ", '*');

                // Password check to fail early here
                // TODO:  Figure out why this fails.
                // ^User is not privileged, authUser requires access to passwd file.
                if (! Users.getUsers().authUser(thisUserName, oldPassword)) {
                    o.println("Old password is incorrect");
                    return;
                }
            }

            o.println("Changing password for " + userName);
            String newPassword = consoleReader.readLine("New password: ", '*');
            String new2Password = consoleReader.readLine("New password (confirm): ", '*');
            if (! newPassword.equals(new2Password)) {
                o.println("Error: Passwords do not match");
                return;
            }

            boolean p = Users.getUsers().setPassword(userName, newPassword);
            if (p) {
                o.println("Password change successful!");
            }
            else {
                o.println("Password change failed...");
            }

        } catch (IOException e) {
            return;
        }
    }


    @ShellCommand(name = "removeuser",
            shortHelp = "Remove a user from the system",
            longHelp = "No arguments are required. \n")
    public static void removeUser(String[] args, InputStream in, OutputStream out, OutputStream err) {
        Logger logger = LoggerFactory.getLogger(UserShellCommands.class);
        logger.info("removeuser with {} arguments", args.length);

        PrintStream o = new PrintStream(out);

        if (args.length != 1) {
            o.print("removeuser does not take any parameters");
	        return;
        }

        ENOSConsoleReader consoleReader = null;
        try {
            consoleReader = new ENOSConsoleReader(in, out, new ENOSTerminal());
        } catch (Exception e) {
            e.printStackTrace();
            return;
        }

        try {
            // Get current username.
            String thisUserName = KernelThread.getCurrentKernelThread().getUser().getName();

            // If this thread is privileged, then ask for a username (because we can remove any user).
            // If not privileged, require password verification to remove user.
            String userName, password;
            if (KernelThread.getCurrentKernelThread().isPrivileged()) {
                userName = consoleReader.readLine("Username (default = " + thisUserName + "): ");
                if (userName.isEmpty()) {
                    userName = thisUserName;
                }
            }
            else {
                userName = KernelThread.getCurrentKernelThread().getUser().getName();
                password = consoleReader.readLine("Password: ", '*');

                if (! Users.getUsers().authUser(thisUserName, password)) {
                    o.println("Password is incorrect");
                    return;
                }
            }

	        // Confirm removal of user account
            o.println("Are you sure you wish to remove this user account?");
            String confirmRemove = consoleReader.readLine("Y/N: ");
            if (confirmRemove.equals("Y")) {
                boolean r = Users.getUsers().removeuser(userName);
                if (r) {
                    o.print("Removed User!");
                } else {
                    o.print("Unable to remove user.");
                }
            } else {
	            o.print("Canceling operation.");
            }

        } catch (IOException e) {
	        return;
        }
    }


	@ShellCommand(name = "ls",
			shortHelp = "List all files in current directory",
			longHelp = "ls <directory (defaults to current directory)>")
	public static void ls(String[] args, InputStream in, OutputStream out, OutputStream err) {
		Logger logger = LoggerFactory.getLogger(UserShellCommands.class);
		logger.info("ls with {} arguments", args.length);

		PrintStream o = new PrintStream(out);

		String userPath = KernelThread.getCurrentKernelThread().getUser().getHomePath().toString();

		// Do argument number check. If no extra args, displays files in current directory;
		// If 1 extra arg, displays files in directory specified by the arg.
		if (args.length == 1 ) {
		} else if (args.length == 2) {

			String dest = args[1];
			if (dest.startsWith("/")) {
				dest = dest.substring(1);
				String newPath = "";
				String currentPath = KernelThread.getCurrentKernelThread().getUser().getHomePath().normalize().toString();
				int occur = currentPath.length() - currentPath.replace("/", "").length();
				for (int i = 0; i < occur; i++) {
					newPath = newPath + "../";
				}
				dest = newPath + Users.getUsers().getEnosRootPath() + "/" + dest;
			}

			userPath = Paths.get(userPath, dest).toString();
		} else {
			o.println("Incorrect number of args");
			return;
		}

		File lsDir = new File (userPath);

		Path normalizedPath = lsDir.toPath().normalize();
		lsDir = new File (Paths.get(normalizedPath.toString()).toString());

		// Store list of files in an array and output.
		String fileList[] = lsDir.list();
		for (String file : fileList) {
			o.println(file);
		}
	}

	@ShellCommand(name = "mkdir",
			shortHelp = "Create a directory in current directory",
			longHelp = "Creates a directory with <name> <directory (default is home directory)>")
	public static void mkdir (String[] args, InputStream in, OutputStream out, OutputStream err) {
		Logger logger = LoggerFactory.getLogger(UserShellCommands.class);
		logger.info("mkdir with {} arguments", args.length);

		PrintStream o = new PrintStream(out);
		boolean mkdir = false;
		User currentUser = KernelThread.getCurrentKernelThread().getUser();
		String userPath = currentUser.getHomePath().toString();

		// Argument checking
		if (args.length < 2) {
			o.println("Usage <name> <directory (default is home)>");
			return;
		}

		// If 2 extra arguments, the last argument is directory where directory will be created.
		if (args.length == 3) {
			String tempFilePath = args[2];
			if (tempFilePath.startsWith("/")) {
				tempFilePath = tempFilePath.substring(1);
				String newPath = "";
				String currentPath = KernelThread.getCurrentKernelThread().getUser().getHomePath().normalize().toString();
				int occur = currentPath.length() - currentPath.replace("/", "").length();
				for (int i = 0; i < occur; i++) {
					newPath = newPath + "../";
				}
				tempFilePath = newPath + Users.getUsers().getEnosRootPath() + "/" + tempFilePath;
			}
			userPath = Paths.get(userPath, tempFilePath).toString();
		}
		// Make sure directory specified exists.
		File storeInDir = new File (userPath);
		if (!storeInDir.exists()) {
			o.print("Directory specified does not exist");
			return;
		}

		// Create new file object with path and name that user specified.
		userPath = Paths.get(userPath, args[1]).toString();
		File newDir = new File (userPath);

		// Create new directory and confirm directory has been created
		try {
			mkdir = Users.getUsers().mkdir(newDir);
		} catch (SecurityException e) {
			o.println("Invalid permissions to access this directory");
		}

		if (mkdir) {
			logger.debug("mkdir success!");
		} else {
			logger.debug("mkdir failure");
			o.println("mkdir failed");
		}
	}


	@ShellCommand(name = "cd",
	             shortHelp = "Change current directory",
	             longHelp = "cd <directory>")
	public static void cd(String[] args, InputStream in, OutputStream out, OutputStream err) {
		Logger logger = LoggerFactory.getLogger(UserShellCommands.class);
		logger.info("cd with {} arguments", args.length);

		PrintStream o = new PrintStream(out);

		String userPath = KernelThread.getCurrentKernelThread().getUser().getHomePath().toString();

		// Argument checking
		if (args.length != 2 ) {
			o.println("Incorrect number of args");
			return;
		}
		// Go to enos root directory if slash is entered
		String dest = args[1];
		if (dest.startsWith("/")) {
			dest = dest.substring(1);
			String newPath = "";
			String currentPath = KernelThread.getCurrentKernelThread().getUser().getHomePath().normalize().toString();
			int occur = currentPath.length() - currentPath.replace("/", "").length();
			for (int i = 0; i < occur; i++) {
				newPath = newPath + "../";
			}
			dest = newPath + Users.getUsers().getEnosRootPath() + "/" + dest;
		}

		File cdDir = new File (Paths.get(userPath, dest).toString());

		Path normalizedPath = cdDir.toPath().normalize();
		cdDir = new File (Paths.get(normalizedPath.toString()).toString());

		// Make sure user has permission to read this directory. If not, outputs error message.
		try {
			cdDir.canRead();
			if (cdDir.exists() & !cdDir.isFile()) {
				KernelThread.getCurrentKernelThread().getUser().setHomePath(Paths.get(userPath, dest));
				logger.debug("cd success");
			} else {
				o.println("Directory does not exist");
			}
		} catch (SecurityException e) {
			o.println("Invalid permissions to access this directory");
		}
	}


	@ShellCommand(name = "cat",
			shortHelp = "Display contents of a file",
			longHelp = "cat <directory>")
	public static void cat(String[] args, InputStream in, OutputStream out, OutputStream err) {
		Logger logger = LoggerFactory.getLogger(UserShellCommands.class);
		logger.info("cat with {} arguments", args.length);

		PrintStream o = new PrintStream(out);

		String userPath = KernelThread.getCurrentKernelThread().getUser().getHomePath().normalize().toString();

		// Argument checking
		if (args.length != 2 ) {
			o.println("Incorrect number of args");
			return;
		}

		String dest = args[1];
		if (dest.startsWith("/")) {
			dest = dest.substring(1);
			String newPath = "";
			String currentPath = KernelThread.getCurrentKernelThread().getUser().getHomePath().normalize().toString();
			int occur = currentPath.length() - currentPath.replace("/", "").length();
			for (int i = 0; i < occur; i++) {
				newPath = newPath + "../";
			}
			dest = newPath + Users.getUsers().getEnosRootPath() + "/" + dest;
		}

		File catFile = new File (Paths.get(userPath).toString());

		Path normalizedPath = catFile.toPath().normalize();
		catFile = new File (Paths.get(normalizedPath.toString()).toString());

		// Make sure user has permission to read this directory. If not, outputs error message.
		try {
			catFile.canRead();
			try {
				BufferedReader read = new BufferedReader(new FileReader(Paths.get(catFile.toString(), dest).toString()));
				String print;
				while((print = read.readLine()) != null) {
					o.println(print);
				}
				read.close();
			} catch (FileNotFoundException e) {
				o.println("File not found");
			} catch (IOException e) {
				e.printStackTrace();
			}

		} catch (SecurityException e) {
			o.println("Invalid permissions to read this file");
			return;
		}
	}


	@ShellCommand(name = "rm",
			shortHelp = "Removes specified file",
			longHelp = "rm <file>")
	public static void rm(String[] args, InputStream in, OutputStream out, OutputStream err) {
		Logger logger = LoggerFactory.getLogger(UserShellCommands.class);
		logger.info("rm with {} arguments", args.length);

		PrintStream o = new PrintStream(out);

		String userPath = KernelThread.getCurrentKernelThread().getUser().getHomePath().toString();

		// Argument checking
		if (args.length != 2 ) {
			o.println("Incorrect number of args");
			return;
		}

		String dest = args[1];
		if (dest.startsWith("/")) {
			dest = dest.substring(1);
			String newPath = "";
			String currentPath = KernelThread.getCurrentKernelThread().getUser().getHomePath().normalize().toString();
			int occur = currentPath.length() - currentPath.replace("/", "").length();
			for (int i = 0; i < occur; i++) {
				newPath = newPath + "../";
			}
			dest = newPath + Users.getUsers().getEnosRootPath() + "/" + dest;
		}

		File rmFile = new File (Paths.get(userPath, dest).toString());

		Path normalizedPath = rmFile.toPath().normalize();
		rmFile = new File (Paths.get(normalizedPath.toString()).toString());

		try {
			// Make sure user has permission to write in this directory. If not, outputs error message.

			rmFile.canWrite();
			if (rmFile.exists()) {
				rmFile.delete();

				// Delete acl file associated with file if it exists
				File aclDelete = new File(Paths.get(normalizedPath.getParent().toString(), ".acl", dest).toString());
				aclDelete.delete();
				logger.debug("rm success");
			} else {
				o.println("File not found");
			}

		} catch (SecurityException e) {
			o.println("Invalid permissions to write in this directory");
		}
	}



	@ShellCommand(name = "$PWD",
			shortHelp = "Displays current directory",
			longHelp = "Displays current directory (no arguments)")
	public static void PWD(String[] args, InputStream in, OutputStream out, OutputStream err) {
		Logger logger = LoggerFactory.getLogger(UserShellCommands.class);
		logger.info("$PWD", args.length);

		PrintStream o = new PrintStream(out);

		String userPath = KernelThread.getCurrentKernelThread().getUser().getHomePath().normalize().toString();
		o.println(userPath + ": is a directory");
	}


}