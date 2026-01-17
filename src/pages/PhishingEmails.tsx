import { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  Mail,
  AlertTriangle,
  CheckCircle,
  Eye,
  Shield,
} from "lucide-react";

interface EmailAnalysis {
  probability: number;
  model_label: string;
  feedback_question?: string;
  composite_score?: number;
  engine?: string;
  enrichment?: Record<string, any>;
}

interface RawEmail {
  id: number;
  sender: string;
  subject: string;
  created_at: string;
  analysis: EmailAnalysis;
  recipients: string[];
  snippet: string;
  body: string;
  has_attachments: boolean;
  is_starred: boolean;
  labels: string[];
}

interface PhishingEmail {
  id: string;
  sender: string;
  subject: string;
  classification: "Phishing" | "Legitimate";
  confidence: number;
  timestamp: string;
  raw: RawEmail;
}

const PhishingEmails = () => {
  const [emails, setEmails] = useState<PhishingEmail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedEmail, setSelectedEmail] =
    useState<PhishingEmail | null>(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/emails/emails")
      .then((res) => {
        if (!res.ok) throw new Error("Fetch failed");
        return res.json();
      })
      .then((data: RawEmail[]) => {
        const mapped = data.map((email) => ({
          id: email.id.toString(),
          sender: email.sender,
          subject: email.subject,
          classification: (
            email.analysis?.model_label === "suspicious"
              ? "Phishing"
              : "Legitimate"
          ) as "Phishing" | "Legitimate",
          confidence: Math.round(
            (email.analysis?.probability ?? 0) * 100
          ),
          timestamp: new Date(email.created_at).toLocaleString(),
          raw: email,
        }));

        setEmails(mapped);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError("Could not load emails");
        setLoading(false);
      });
  }, []);

  const classificationBadge = (
    type: "Phishing" | "Legitimate",
    confidence: number
  ) => {
    if (type === "Phishing") {
      return (
        <Badge variant="destructive">
          <AlertTriangle className="h-3 w-3 mr-1" />
          Phishing ({confidence}%)
        </Badge>
      );
    }
    return (
      <Badge className="bg-green-100 text-green-700 border-green-300">
        <CheckCircle className="h-3 w-3 mr-1" />
        Legitimate ({confidence}%)
      </Badge>
    );
  };

  if (loading) {
    return <p className="text-muted-foreground">Loading emails...</p>;
  }

  if (error) {
    return <p className="text-red-500">{error}</p>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">
            Phishing Email Detection
          </h1>
          <p className="text-muted-foreground">
            AI-powered analysis from FastAPI
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <AlertTriangle className="text-red-500" />
            <div>
              <p className="text-xl font-bold">
                {
                  emails.filter(
                    (e) => e.classification === "Phishing"
                  ).length
                }
              </p>
              <p className="text-sm text-muted-foreground">
                Phishing
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <CheckCircle className="text-green-500" />
            <div>
              <p className="text-xl font-bold">
                {
                  emails.filter(
                    (e) => e.classification === "Legitimate"
                  ).length
                }
              </p>
              <p className="text-sm text-muted-foreground">
                Legitimate
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <Mail />
            <div>
              <p className="text-xl font-bold">
                {emails.length}
              </p>
              <p className="text-sm text-muted-foreground">
                Total Emails
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <Shield className="text-blue-500" />
            <div>
              <p className="text-xl font-bold">ML</p>
              <p className="text-sm text-muted-foreground">
                Detection Engine
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>Email Analysis</CardTitle>
          <CardDescription>
            /api/emails/emails
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Sender</TableHead>
                <TableHead>Subject</TableHead>
                <TableHead>Classification</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {emails.map((email) => (
                <TableRow key={email.id}>
                  <TableCell>{email.sender}</TableCell>
                  <TableCell className="max-w-xs truncate">
                    {email.subject}
                  </TableCell>
                  <TableCell>
                    {classificationBadge(
                      email.classification,
                      email.confidence
                    )}
                  </TableCell>
                  <TableCell>{email.timestamp}</TableCell>
                  <TableCell>
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() =>
                            setSelectedEmail(email)
                          }
                        >
                          <Eye className="h-4 w-4 mr-1" />
                          View
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-md max-h-[70vh] overflow-auto space-y-4 bg-gray-900 text-gray-100 p-4 rounded-lg">

                        <DialogHeader>
                          <DialogTitle>Email Details</DialogTitle>
                          <DialogDescription>
                            Raw analysis from backend
                          </DialogDescription>
                        </DialogHeader>

                        {selectedEmail && (
                          <div className="space-y-4 text-sm">
                            {/* Sender & Subject */}
                            <div className="p-3 border border-gray-700 rounded-lg bg-gray-800">
                              <p><b>From:</b> {selectedEmail.sender}</p>
                              <p><b>To:</b> {selectedEmail.raw.recipients.join(", ")}</p>
                              <p><b>Subject:</b> {selectedEmail.subject}</p>
                              <p><b>Date:</b> {selectedEmail.timestamp}</p>
                              <p><b>Starred:</b> {selectedEmail.raw.is_starred ? "Yes" : "No"}</p>
                            </div>

                            {/* Body & Snippet */}
                            <div className="p-3 border border-gray-700 rounded-lg bg-gray-800">
                              <p><b>Snippet:</b> {selectedEmail.raw.snippet}</p>
                              <p><b>Body:</b></p>
                              <div className="p-2 bg-gray-700 border border-gray-600 rounded max-h-40 overflow-auto">
                                {selectedEmail.raw.body || "No body available"}
                              </div>
                            </div>

                            {/* Attachments */}
                            <div className="p-3 border border-gray-700 rounded-lg bg-gray-800 flex items-center gap-2">
                              <b>Attachments:</b>
                              {selectedEmail.raw.has_attachments ? (
                                <Badge className="bg-red-600 text-white">Yes</Badge>
                              ) : (
                                <Badge className="bg-gray-600 text-gray-100">No</Badge>
                              )}
                            </div>

                            {/* Labels */}
                            <div className="p-3 border border-gray-700 rounded-lg bg-gray-800 flex flex-wrap gap-2">
                              <b>Labels:</b>
                              {selectedEmail.raw.labels.map((label) => (
                                <Badge key={label} className="bg-blue-600 text-white">{label}</Badge>
                              ))}
                            </div>

                            {/* Analysis */}
                            <div className="p-3 border border-gray-700 rounded-lg bg-gray-800 space-y-1">
                              <p><b>Model Label:</b> {selectedEmail.raw.analysis?.model_label}</p>
                              <p><b>Probability:</b> {(selectedEmail.raw.analysis?.probability ?? 0) * 100}%</p>
                              <p><b>Composite Score:</b> {selectedEmail.raw.analysis?.composite_score}</p>
                              <p><b>Engine:</b> {selectedEmail.raw.analysis?.engine}</p>
                              <p><b>Feedback:</b> {selectedEmail.raw.analysis?.feedback_question}</p>

                              <div className="mt-2 p-2 bg-gray-700 border border-gray-600 rounded">
                                <p className="font-semibold">Enrichment:</p>
                                <ul className="list-disc list-inside text-xs">
                                  {selectedEmail.raw.analysis?.enrichment &&
                                    Object.entries(selectedEmail.raw.analysis.enrichment).map(
                                      ([key, value]) => (
                                        <li key={key}>
                                          <b>{key}:</b> {value?.toString()}
                                        </li>
                                      )
                                    )}
                                </ul>
                              </div>
                            </div>
                          </div>
                        )}
                      </DialogContent>

                    </Dialog>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default PhishingEmails;
