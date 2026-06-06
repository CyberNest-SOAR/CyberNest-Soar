import { useState } from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AlertTriangle } from "lucide-react";

interface ConfirmActionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  actionLabel: string;
  actionVariant?: "destructive" | "default" | "warning";
  targetLabel: string;
  requireReason?: boolean;
  requireTicketId?: boolean;
  onConfirm: (params: { reason: string; ticketId: string }) => void;
}

export function ConfirmActionDialog({
  open,
  onOpenChange,
  title,
  description,
  actionLabel,
  actionVariant = "destructive",
  targetLabel,
  requireReason = true,
  requireTicketId = false,
  onConfirm,
}: ConfirmActionDialogProps) {
  const [reason, setReason] = useState("");
  const [ticketId, setTicketId] = useState("");

  const handleConfirm = () => {
    onConfirm({ reason, ticketId });
    setReason("");
    setTicketId("");
    onOpenChange(false);
  };

  const isDisabled = (requireReason && !reason.trim()) || (requireTicketId && !ticketId.trim());

  const variantStyles: Record<string, string> = {
    destructive: "bg-rose-600 hover:bg-rose-700 text-white",
    warning: "bg-amber-600 hover:bg-amber-700 text-white",
    default: "bg-primary hover:bg-primary/90 text-white",
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent className="border-border/40 shadow-2xl max-w-md">
        <AlertDialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className={`p-2.5 rounded-xl ${
              actionVariant === "destructive" 
                ? "bg-rose-500/10 border border-rose-500/20 text-rose-500" 
                : actionVariant === "warning"
                ? "bg-amber-500/10 border border-amber-500/20 text-amber-500"
                : "bg-primary/10 border border-primary/20 text-primary"
            }`}>
              <AlertTriangle className="h-5 w-5" />
            </div>
            <AlertDialogTitle className="text-base font-bold">{title}</AlertDialogTitle>
          </div>
          <AlertDialogDescription className="text-sm text-muted-foreground">
            {description}
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="space-y-4 py-2">
          <div className="rounded-xl bg-muted/20 border border-border/30 p-3">
            <p className="text-[10px] uppercase tracking-widest font-bold text-muted-foreground/60 mb-1">TARGET</p>
            <p className="font-mono text-sm font-bold text-foreground break-all">{targetLabel}</p>
          </div>

          {requireReason && (
            <div className="space-y-1.5">
              <Label htmlFor="reason" className="text-[11px] uppercase tracking-wider font-bold text-muted-foreground/80">
                Justification <span className="text-rose-400">*</span>
              </Label>
              <Input
                id="reason"
                placeholder="e.g. Suspicious outbound traffic to known C2"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="bg-background/50 border-border/40 text-xs"
                autoFocus
              />
            </div>
          )}

          {requireTicketId && (
            <div className="space-y-1.5">
              <Label htmlFor="ticketId" className="text-[11px] uppercase tracking-wider font-bold text-muted-foreground/80">
                Associated Ticket ID
              </Label>
              <Input
                id="ticketId"
                placeholder="e.g. INC-2026-0042"
                value={ticketId}
                onChange={(e) => setTicketId(e.target.value)}
                className="bg-background/50 border-border/40 text-xs font-mono"
              />
            </div>
          )}
        </div>

        <AlertDialogFooter className="gap-2">
          <AlertDialogCancel className="text-xs font-bold h-9">Cancel</AlertDialogCancel>
          <AlertDialogAction
            disabled={isDisabled}
            onClick={handleConfirm}
            className={`text-xs font-bold h-9 uppercase tracking-wider ${variantStyles[actionVariant]}`}
          >
            {actionLabel}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
