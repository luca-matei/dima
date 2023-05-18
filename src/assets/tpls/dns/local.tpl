zone "%ZONE%" {
    type master;
    file "/etc/bind/db.%ZONE%";
    notify no;
};
