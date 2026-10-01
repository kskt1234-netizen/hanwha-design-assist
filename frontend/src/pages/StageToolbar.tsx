import { Button, Popconfirm, Space, Tag } from "antd";

const STATUS: Record<string, { color: string; label: string }> = {
  EMPTY: { color: "default", label: "초안 없음" },
  DRAFT: { color: "orange", label: "초안 (미승인)" },
  APPROVED: { color: "green", label: "승인됨" },
};

interface Props {
  status: string;
  dirty: boolean;
  busy: boolean;
  canGenerate: boolean;
  onGenerate: () => void;
  onSave: () => void;
  onApprove: () => void;
}

export default function StageToolbar({ status, dirty, busy, canGenerate, onGenerate, onSave, onApprove }: Props) {
  const s = STATUS[status] ?? STATUS.EMPTY;
  return (
    <Space style={{ marginBottom: 16 }} wrap>
      <Tag color={s.color}>{s.label}</Tag>
      <Popconfirm
        title="AI 초안을 다시 생성하면 현재 내용이 바뀝니다. 계속할까요?"
        disabled={status === "EMPTY"}
        onConfirm={onGenerate}
      >
        <Button loading={busy} disabled={!canGenerate} onClick={status === "EMPTY" ? onGenerate : undefined}>
          AI 초안 생성
        </Button>
      </Popconfirm>
      <Button onClick={onSave} disabled={!dirty || busy}>수정 저장</Button>
      <Button type="primary" onClick={onApprove} disabled={dirty || busy || status === "EMPTY"}>승인</Button>
    </Space>
  );
}
