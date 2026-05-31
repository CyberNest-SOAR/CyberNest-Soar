module BruteForce;

export {
    redef enum Notice::Type += { SSH_Brute_Force };
}

# Track failed SSH attempts per IP
global ssh_failures: table[addr] of count &default=0;

event ssh_auth_failed(c: connection)
{
    local attacker = c$id$orig_h;
    ssh_failures[attacker] += 1;

    if ( ssh_failures[attacker] > 5 )
    {
        NOTICE([
            $note = SSH_Brute_Force,
            $msg  = fmt("SSH brute force suspected from %s (%d failures)", attacker, ssh_failures[attacker]),
            $conn = c
        ]);
    }
}
