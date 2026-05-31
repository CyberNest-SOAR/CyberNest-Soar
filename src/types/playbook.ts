export interface PlaybookRule {
  name: string;
  enabled: boolean;
  conditions: Record<string, any>;
  action: string;
  confidence: number;
  automation_level: string;
  reason: string;
  triggers: number;
}
