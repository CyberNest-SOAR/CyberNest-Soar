-- Create table for attack documentation and resources
CREATE TABLE public.attack_resources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  url TEXT NOT NULL,
  category TEXT NOT NULL,
  icon TEXT NOT NULL DEFAULT 'FileText',
  created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.attack_resources ENABLE ROW LEVEL SECURITY;

-- Admins can manage resources
CREATE POLICY "Admins can manage attack resources"
ON public.attack_resources
FOR ALL
TO authenticated
USING (has_role(auth.uid(), 'admin'::app_role))
WITH CHECK (has_role(auth.uid(), 'admin'::app_role));

-- SOC analysts and admins can view resources
CREATE POLICY "Analysts and admins can view attack resources"
ON public.attack_resources
FOR SELECT
TO authenticated
USING (
  has_role(auth.uid(), 'soc_analyst'::app_role) OR 
  has_role(auth.uid(), 'admin'::app_role)
);

-- Add trigger for updated_at
CREATE TRIGGER update_attack_resources_updated_at
BEFORE UPDATE ON public.attack_resources
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at();