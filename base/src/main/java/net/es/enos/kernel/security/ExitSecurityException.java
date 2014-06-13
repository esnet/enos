package net.es.enos.kernel.security;

/**
 * This class is used to distinguish a SecurityException generated by checkExit() from other SecurityException.
 * This allows the python interpreter to exit without displaying an error message
 */
public class ExitSecurityException extends SecurityException {
    public ExitSecurityException(String s) {
        super(s);
    }
}