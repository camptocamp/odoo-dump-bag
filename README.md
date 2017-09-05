# Odoo Dump Bag

https://jira.camptocamp.com/browse/BS-62


## GPG Keys handling

We share a GPG Private key for the internal developers of the department.
For the external developers that may need to decrypt the dumps, a nominative
key must be created for each person, so we can remove them at some point.

The public keys are configured in the stack and is used to encrypt the files.
The private keys must be kept in a safe place and are used to decrypt the files
on the developers computers.

### Create a new key

```
$ gpg --gen-key
```

* Select `(1)` RSA and RSA (default)
* Type `4096` as keysize
* Set the key to not expire (`0`)
* Choose a name and set the email address of the person that must
  be able to decrypt the dumps
* Set a passphrase

### Export the keys

Export the private key:

```
gpg --export-secret-key -a "User Name (or email)" > private.key

```

Export the public key:

```
gpg --export -a "User Name (or email)" > public.key

```

Store the private key in a safe place.

### Configure public keys

The public keys must be set in the server container in an environment variable
`GPG_IMPORT_PUBLIC_KEYS`.  All the key  will be imported at the start of the
container. Please set a comment above each key so we can easily see what
the keys are without importing them before.

Example of the content for this environment variable:

```
# Camptocamp Business Devs (Used for odoo-dumps) <business@camptocamp.com>
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1

mQINBFmuUTwBEACSEyQ7Svz3HNBCMJVZ3sagrZRqvretrvn+txSmhKaFS7QZ0oc+
....
=pula
-----END PGP PUBLIC KEY BLOCK-----
# Joe Bar (Used for odoo-dumps) <joe.bar@example.com>
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1

mQMuBExgG+4RCACFRdLa8JRrLOZYOZXyHZ0dqAul/FcaI3K4NnBNs9iv14XKcwUt
...
=JcEU
-----END PGP PUBLIC KEY BLOCK-----
```
