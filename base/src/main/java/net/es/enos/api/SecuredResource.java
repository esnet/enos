package net.es.enos.api;

/**
 * A resources that implements SecureResource is a Resource that requires to be privileged in order to change
 * or modify the list of children and parents. This allows to have a secured and verifiable graph of resources,
 * i.e. resources depending on other resources.
 */
public interface SecuredResource {
}
