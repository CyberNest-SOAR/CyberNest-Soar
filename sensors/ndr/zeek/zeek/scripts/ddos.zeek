module DDoS;

export {
    redef enum Notice::Type += { Possible_DDoS };
}

global conn_counter: table[addr] of count &default=0;

event connection_established(c: connection)
{
    conn_counter[c$id$orig_h] += 1;

    if ( conn_counter[c$id$orig_h] > 100 )
    {
        NOTICE([$note=Possible_DDoS,
                $msg=fmt("High connection rate from %s", c$id$orig_h),
                $conn=c]);
    }
}
