import { useEffect, useState } from "react";
import { Alert, Button, Card, Checkbox, Col, Collapse, Input, InputNumber, Row, Select, Space, Table, Tabs } from "antd";
import { api } from "../api";
import type { Attribute, DesignState, Entity, Relationship } from "../types";
import { withKeys } from "./withKeys";
import Mermaid from "./Mermaid";

interface Props {
  projectId: number;
  revision: number;
  state: DesignState;
  dirty: boolean;
  onChange: (patch: Partial<DesignState>) => void;
}

const TYPES = ["BIGINT", "INTEGER", "VARCHAR", "TEXT", "NUMERIC", "BOOLEAN", "DATE", "TIMESTAMP"];
const NEW_ATTR: Attribute = {
  name: "", logical_name: "", data_type: "VARCHAR", length: 100, nullable: true, is_pk: false, is_unique: false, default: null,
};

export default function DataModelTab({ projectId, revision, state, dirty, onChange }: Props) {
  const [ddl, setDdl] = useState("");
  const [diagram, setDiagram] = useState("");
  const { entities, relationships } = state;

  useEffect(() => {
    api.ddl(projectId).then(setDdl);
    api.mermaid(projectId).then(setDiagram);
  }, [projectId, revision]);

  const setEntity = (i: number, patch: Partial<Entity>) =>
    onChange({ entities: entities.map((e, j) => (j === i ? { ...e, ...patch } : e)) });
  const setAttr = (ei: number, ai: number, patch: Partial<Attribute>) =>
    setEntity(ei, { attributes: entities[ei].attributes.map((a, j) => (j === ai ? { ...a, ...patch } : a)) });
  const setRel = (i: number, patch: Partial<Relationship>) =>
    onChange({ relationships: relationships.map((r, j) => (j === i ? { ...r, ...patch } : r)) });

  const tableOptions = entities.map((e) => ({ value: e.table_name, label: e.table_name }));
  const featureOptions = state.features.map((f) => ({ value: f.code, label: `${f.code} ${f.name}` }));

  return (
    <Row gutter={16}>
      <Col xs={24} xl={13}>
        <Collapse
          items={entities.map((e, ei) => ({
            key: String(ei),
            label: `${e.table_name} ${e.logical_name ? `(${e.logical_name})` : ""} · 컬럼 ${e.attributes.length}개`,
            children: (
              <Space direction="vertical" style={{ width: "100%" }}>
                <Space wrap>
                  <Input addonBefore="테이블" value={e.table_name} onChange={(x) => setEntity(ei, { table_name: x.target.value })} />
                  <Input addonBefore="논리명" value={e.logical_name} onChange={(x) => setEntity(ei, { logical_name: x.target.value })} />
                  <Button danger onClick={() => onChange({ entities: entities.filter((_, j) => j !== ei) })}>테이블 삭제</Button>
                </Space>
                <Select mode="multiple" placeholder="이 테이블을 쓰는 기능" style={{ width: "100%" }} value={e.feature_codes}
                  options={featureOptions} optionLabelProp="value" onChange={(feature_codes) => setEntity(ei, { feature_codes })} />
                <Table
                  rowKey="key"
                  size="small"
                  pagination={false}
                  dataSource={withKeys(e.attributes)}
                  columns={[
                    { title: "컬럼", render: (_, a, ai) => <Input value={a.name} onChange={(x) => setAttr(ei, ai, { name: x.target.value })} /> },
                    { title: "논리명", render: (_, a, ai) => <Input value={a.logical_name} onChange={(x) => setAttr(ei, ai, { logical_name: x.target.value })} /> },
                    {
                      title: "타입", width: 130,
                      render: (_, a, ai) => (
                        <Select value={a.data_type} style={{ width: "100%" }} options={TYPES.map((t) => ({ value: t, label: t }))}
                          onChange={(data_type) => setAttr(ei, ai, { data_type })} />
                      ),
                    },
                    { title: "길이", width: 80, render: (_, a, ai) => <InputNumber value={a.length} onChange={(length) => setAttr(ei, ai, { length })} /> },
                    { title: "PK", width: 45, render: (_, a, ai) => <Checkbox checked={a.is_pk} onChange={(x) => setAttr(ei, ai, { is_pk: x.target.checked })} /> },
                    { title: "NULL", width: 50, render: (_, a, ai) => <Checkbox checked={a.nullable} onChange={(x) => setAttr(ei, ai, { nullable: x.target.checked })} /> },
                    { title: "UK", width: 45, render: (_, a, ai) => <Checkbox checked={a.is_unique} onChange={(x) => setAttr(ei, ai, { is_unique: x.target.checked })} /> },
                    {
                      title: "", width: 40,
                      render: (_, __, ai) => (
                        <Button size="small" type="text" danger onClick={() => setEntity(ei, { attributes: e.attributes.filter((_, j) => j !== ai) })}>✕</Button>
                      ),
                    },
                  ]}
                />
                <Button size="small" onClick={() => setEntity(ei, { attributes: [...e.attributes, { ...NEW_ATTR }] })}>컬럼 추가</Button>
              </Space>
            ),
          }))}
        />
        <Button style={{ margin: "8px 0 16px" }} onClick={() => onChange({
          entities: [...entities, {
            table_name: `new_table_${entities.length + 1}`, logical_name: "", description: "", feature_codes: [],
            attributes: [{ ...NEW_ATTR, name: "id", data_type: "BIGINT", length: null, nullable: false, is_pk: true }],
          }],
        })}>
          테이블 추가
        </Button>

        <Card size="small" title="관계 (FK)">
          <Table
            rowKey="key"
            size="small"
            pagination={false}
            dataSource={withKeys(relationships)}
            columns={[
              { title: "부모", render: (_, r, i) => <Select value={r.to_table} style={{ width: 150 }} options={tableOptions} onChange={(to_table) => setRel(i, { to_table })} /> },
              {
                title: "관계", width: 90,
                render: (_, r, i) => (
                  <Select value={r.cardinality} options={["1:1", "1:N", "N:M"].map((c) => ({ value: c, label: c }))}
                    onChange={(cardinality) => setRel(i, { cardinality })} />
                ),
              },
              { title: "자식", render: (_, r, i) => <Select value={r.from_table} style={{ width: 150 }} options={tableOptions} onChange={(from_table) => setRel(i, { from_table })} /> },
              { title: "FK 컬럼", render: (_, r, i) => <Input value={r.fk_column} onChange={(x) => setRel(i, { fk_column: x.target.value })} /> },
              {
                title: "", width: 40,
                render: (_, __, i) => <Button size="small" type="text" danger onClick={() => onChange({ relationships: relationships.filter((_, j) => j !== i) })}>✕</Button>,
              },
            ]}
          />
          <Button size="small" style={{ marginTop: 8 }} disabled={entities.length < 2} onClick={() => onChange({
            relationships: [...relationships, {
              from_table: entities[1]?.table_name ?? "", to_table: entities[0]?.table_name ?? "", fk_column: "", cardinality: "1:N", on_delete: "RESTRICT",
            }],
          })}>
            관계 추가
          </Button>
        </Card>
      </Col>
      <Col xs={24} xl={11}>
        {dirty && <Alert type="info" showIcon style={{ marginBottom: 8 }} message="수정 내용을 저장하면 ERD와 DDL에 반영됩니다." />}
        <Tabs
          items={[
            { key: "erd", label: "ERD", children: diagram.includes("{") ? <Mermaid code={diagram} /> : "데이터 모델이 없습니다" },
            {
              key: "ddl", label: "DDL (PostgreSQL)",
              children: (
                <>
                  <Button size="small" style={{ marginBottom: 8 }} onClick={() => {
                    const url = URL.createObjectURL(new Blob([ddl], { type: "text/sql" }));
                    Object.assign(document.createElement("a"), { href: url, download: "schema.sql" }).click();
                    URL.revokeObjectURL(url);
                  }}>
                    .sql 다운로드
                  </Button>
                  <pre style={{ background: "#fafafa", padding: 12, maxHeight: 600, overflow: "auto", fontSize: 12 }}>{ddl}</pre>
                </>
              ),
            },
          ]}
        />
      </Col>
    </Row>
  );
}
