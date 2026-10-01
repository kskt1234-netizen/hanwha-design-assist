export type ReqType = "FUNCTIONAL" | "NON_FUNCTIONAL";
export type Priority = "HIGH" | "MEDIUM" | "LOW";
export type Cardinality = "1:1" | "1:N" | "N:M";
export type StageKey = "requirements" | "features" | "data_model";

export interface Requirement { code: string; text: string; type: ReqType }
export interface Feature {
  code: string; name: string; description: string; priority: Priority; requirement_codes: string[];
}
export interface Attribute {
  name: string; logical_name: string; data_type: string; length: number | null;
  nullable: boolean; is_pk: boolean; is_unique: boolean; default: string | null;
}
export interface Entity {
  table_name: string; logical_name: string; description: string; attributes: Attribute[]; feature_codes: string[];
}
export interface Relationship {
  from_table: string; to_table: string; fk_column: string; cardinality: Cardinality; on_delete: string;
}
export interface DesignState {
  requirements: Requirement[]; features: Feature[]; entities: Entity[]; relationships: Relationship[];
}
export interface Project {
  id: number; name: string; domain: string; stage_status: Record<StageKey, string>; document_count: number;
}
export interface Domain { code: string; name: string }
export interface DocumentInfo { id: number; filename: string; length: number }
export interface TraceRow {
  requirement_code: string; requirement_text: string; requirement_type: ReqType;
  feature_code: string | null; feature_name: string | null; tables: string[];
}
export interface Issue {
  id: number; rule_code: string; severity: "ERROR" | "WARN" | "INFO";
  target_type: string; target_code: string; message: string; status: "OPEN" | "RESOLVED" | "IGNORED";
}
