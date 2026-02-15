module BruteForce;

export {
    redef enum Notice::Type += {
        Brute_Force_Attack
    };
}

const fail_threshold = 5;

global failures: table[addr] of count &default=0;

event ssh_auth_failed(c: connection)
{
    local ip = c$id$orig_h;

    failures[ip] += 1;

    if ( failures[ip] >= fail_threshold )
    {
        NOTICE([
            $note=Brute_Force_Attack,
            $msg=fmt("SSH brute force suspected from %s", ip),
            $conn=c
        ]);

        delete failures[ip];
    }
}
