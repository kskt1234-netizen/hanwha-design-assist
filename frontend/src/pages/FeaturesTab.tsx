import { Button, Input, Select, Table } from "antd";
import type { Feature, Requirement } from "../types";
import { withKeys } from "./withKeys";

interface Props { value: Feature[]; requirements: Requirement[]; onChange: (v: Feature[]) => void }

export default function FeaturesTab({ value, requirements, onChange }: Props) {
  const set = (i: number, patch: Partial<Feature>) => onChange(value.map((f, j) => (j === i ? { ...f, ...patch } : f)));
  const reqOptions = requirements.map((r) => ({ value: r.code, label: `${r.code} ${r.text.slice(0, 30)}` }));

  return (
    <>
      <Table
        rowKey="key"
        dataSource={withKeys(value)}
        pagination={false}
        size="small"
        columns={[
          { title: "기능 ID", width: 100, render: (_, f, i) => <Input value={f.code} onChange={(e) => set(i, { code: e.target.value })} /> },
          { title: "기능명", width: 200, render: (_, f, i) => <Input value={f.name} onChange={(e) => set(i, { name: e.target.value })} /> },
          { title: "설명", render: (_, f, i) => <Input.TextArea autoSize value={f.description} onChange={(e) => set(i, { description: e.target.value })} /> },
          {
            title: "우선순위", width: 110,
            render: (_, f, i) => (
              <Select value={f.priority} style={{ width: "100%" }} onChange={(priority) => set(i, { priority })}
                options={[{ value: "HIGH", label: "상" }, { value: "MEDIUM", label: "중" }, { value: "LOW", label: "하" }]} />
            ),
          },
          {
            title: "근거 요구사항", width: 220,
            render: (_, f, i) => (
              <Select mode="multiple" value={f.requirement_codes} style={{ width: "100%" }} options={reqOptions}
                optionLabelProp="value" onChange={(requirement_codes) => set(i, { requirement_codes })} />
            ),
          },
          { title: "", width: 60, render: (_, __, i) => <Button size="small" danger onClick={() => onChange(value.filter((_, j) => j !== i))}>삭제</Button> },
        ]}
      />
      <Button
        style={{ marginTop: 8 }}
        onClick={() => onChange([...value, {
          code: `FN-${String(value.length + 1).padStart(3, "0")}`, name: "", description: "", priority: "MEDIUM", requirement_codes: [],
        }])}
      >
        기능 추가
      </Button>
    </>
  );
}
