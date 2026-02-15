module DDoS;

export {
    redef enum Notice::Type += {
        Potential_DDoS
    };
}

const threshold = 100;

global conn_count: table[addr] of count &default=0;

event connection_established(c: connection)
{
    conn_count[c$id$orig_h] += 1;
}

event zeek_done()
{
    for ( ip in conn_count )
    {
        if ( conn_count[ip] > threshold )
        {
            NOTICE([
                $note=Potential_DDoS,
                $msg=fmt("High connections from %s (%d)", ip, conn_count[ip])
            ]);
        }
    }
}
