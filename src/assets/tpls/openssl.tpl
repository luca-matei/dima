[req]
default_bits       = 4096
default_keyfile    = localhost.key
distinguished_name = req_distinguished_name
req_extensions     = req_ext
x509_extensions    = v3_ca

[req_distinguished_name]
countryName                 = RO
countryName_default         = RO
stateOrProvinceName         = Bucharest
stateOrProvinceName_default = Bucharest
localityName                = Bucharest
localityName_default        = Bucharest
organizationName            = lucamatei
organizationName_default    = lucamatei
organizationalUnitName      = dima
organizationalUnitName_default = dima
commonName                  = Luca Matei
commonName_default          = Luca Matei
commonName_max              = 64

[req_ext]
subjectAltName = @alt_names

[v3_ca]
subjectAltName = @alt_names

[alt_names]
DNS.1   = localhost
DNS.2   = 127.0.0.1
