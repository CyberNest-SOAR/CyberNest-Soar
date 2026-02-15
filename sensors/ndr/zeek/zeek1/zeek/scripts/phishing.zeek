module Phishing;

export {
    redef enum Notice::Type += {
        Phishing_Domain,
        Suspicious_Email_Link
    };
}

const suspicious_keywords = /login|verify|update|secure|account/i;

event http_request(c: connection, method: string, host: string, uri: string,
                   version: string)
{
    if ( host == "" ) return;

    if ( suspicious_keywords in host || suspicious_keywords in uri )
    {
        NOTICE([
            $note=Phishing_Domain,
            $msg=fmt("Possible phishing URL: %s%s", host, uri),
            $conn=c
        ]);
    }
}
