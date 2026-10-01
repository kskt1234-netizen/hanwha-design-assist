import { Button, Input, Select, Table } from "antd";
import type { Requirement } from "../types";
import { withKeys } from "./withKeys";

interface Props { value: Requirement[]; onChange: (v: Requirement[]) => void }

export default function RequirementsTab({ value, onChange }: Props) {
  const set = (i: number, patch: Partial<Requirement>) => onChange(value.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  const nextCode = () => `REQ-${String(value.length + 1).padStart(3, "0")}`;

  return (
    <>
      <Table
        rowKey="key"
        dataSource={withKeys(value)}
        pagination={false}
        size="small"
        columns={[
          { title: "ID", width: 110, render: (_, r, i) => <Input value={r.code} onChange={(e) => set(i, { code: e.target.value })} /> },
          { title: "요구사항", render: (_, r, i) => <Input.TextArea autoSize value={r.text} onChange={(e) => set(i, { text: e.target.value })} /> },
          {
            title: "분류", width: 130,
            render: (_, r, i) => (
              <Select value={r.type} style={{ width: "100%" }} onChange={(type) => set(i, { type })}
                options={[{ value: "FUNCTIONAL", label: "기능" }, { value: "NON_FUNCTIONAL", label: "비기능" }]} />
            ),
          },
          { title: "", width: 60, render: (_, __, i) => <Button size="small" danger onClick={() => onChange(value.filter((_, j) => j !== i))}>삭제</Button> },
        ]}
      />
      <Button style={{ marginTop: 8 }} onClick={() => onChange([...value, { code: nextCode(), text: "", type: "FUNCTIONAL" }])}>
        요구사항 추가
      </Button>
    </>
  );
}
