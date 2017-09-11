[![Build Status](https://travis-ci.com/camptocamp/odoo-dump-bag.svg?token=3A3ZhwttEcmdqp7JzQb7&branch=master)](https://travis-ci.com/camptocamp/odoo-dump-bag)

# Odoo Dump Bag

https://jira.camptocamp.com/browse/BS-62

## Pre-requisite

The debian packages required are `postgresql-client`, `gnupg`. They are included in the Docker image.

Test dependencies are: `pytest` and `mock`, which are installed in the Docker image too.

## Configuration

The server application is configured with environment variables:

* `FLASK_SECRET_KEY`: must be unique and random (e.g. `os.urandom(24)`)
* `FLASK_DEBUG`: set to true only for dev
* `BAG_EXCLUDE_DATABASE`: database to exclude from the dumps, separated by commas. Recommended: `template0,template1,postgres`
* `BAG_DB_KIND`: `static`/`postgres`
* `BAG_STORAGE_KIND`: `local`/`s3`
* `BAG_ENCRYPTION_KIND: `none`/`gpg`

An example for docker-compose can be found in [docker-compose.example.yml](docker-compose.example.yml)

### Configuration for DB

#### static

Only used for dev, instead of reading the list of databases from a PostgreSQL server, it returns a hardcoded list. The dumps are generated with dummy content.

#### postgres

It uses the `psql` and `pg_dump` commands to list the databases and generate the dumps. Variables:

* `BAG_DB_HOST`: host of the PostgreSQL server
* `BAG_DB_PORT`: port of the PostgreSQL server
* `BAG_DB_USER`: user to use for database listing and dumps
* `BAG_DB_PASSWORD`:  password for the user

Dumps are created with the options `--format=c` and `--no-owner`.

### Configuration for Storage

#### local

Dumps are stored in a local directory. Variables:

* `BAG_STORAGE_LOCAL_DIR`: path to the directory to save the dumps

#### s3

It uses the `aws s3` and `aws s3api` commands to list and copy the files around. Variables:

* `BAG_S3_BUCKET_NAME`: name of the S3 bucket
* `BAG_S3_ACCESS_KEY`: access key for the S3 bucket
* `BAG_S3_SECRET_ACCESS_KEY`: secret access key for the S3 bucket

### Configuration for Encryption

#### none

Dumps are stored without encryption

#### gpg

It uses the `gpg` command. It encrypts the dumps for a list of recipients whose keys must be on the server. With the Docker image, the public keys can be imported with the environment variable `GPG_IMPORT_PUBLIC_KEYS`.

Variables for the encryption:

* `BAG_GPG_RECIPIENTS`: list of recipients separated by commas, only these recipients will be able to decrypt the dumps as long as they have the private key

## Central configuration

When using the Docker image, GPG public keys and recipients can be
automatically configured from another dump bag server.

Instead of `GPG_IMPORT_PUBLIC_KEYS` and `BAG_GPG_RECIPIENTS`,
configure the keys:

* `GPG_IMPORT_PUBLIC_KEYS_FROM_URL`: URL of another dump bag
  server providing the public keys. The route is `/keys`:
  http://dump-bag/keys
* `GPG_RECIPIENTS_FROM_URL`: URL of another dump bag server
  providing the list of recipients. The route is `/recipients`:
  http://dump-bag/recipients

Beware, this configuration is only read at the start of the container, so a
change in the main configuration requires a restart. In the future, this could
be checked regularly at runtime.

If the Docker image could not be used, it could be done with an initialization script with this snippet:

```
curl -s http://dump-bag/keys | gpg --import
BAG_GPG_RECIPIENTS=$(curl -s http://dump-bag/recipients)
export BAG_GPG_RECIPIENTS
```

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
