module Phishing;

export {
    redef enum Notice::Type += {
        Phishing_Attempt
    };
}

event http_request(c: connection, method: string, host: string, uri: string,
                   version: string)
{
    if ( host == "" )
        return;

    local suspicious = /secure|login|verify|account|update|bank|password/i;

    if ( host == suspicious || uri == suspicious )
    {
        NOTICE([
            $note=Phishing_Attempt,
            $msg=fmt("Possible phishing attempt: host=%s uri=%s", host, uri),
            $conn=c
        ]);
    }
}
