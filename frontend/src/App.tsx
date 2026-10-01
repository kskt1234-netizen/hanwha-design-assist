import { useCallback, useEffect, useState } from "react";
import { App as AntApp, Button, Empty, Form, Input, Layout, Menu, Modal, Select, Typography } from "antd";
import { api } from "./api";
import type { Domain, Project } from "./types";
import ProjectView from "./pages/ProjectView";

export default function App() {
  const { message } = AntApp.useApp();
  const [projects, setProjects] = useState<Project[]>([]);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);
  const [form] = Form.useForm<{ name: string; domain: string }>();

  const load = useCallback(async () => {
    const list = await api.projects();
    setProjects(list);
    setSelected((cur) => cur ?? list[0]?.id ?? null);
  }, []);

  useEffect(() => {
    load().catch((e) => message.error(e.message));
    api.domains().then(setDomains).catch(() => undefined);
  }, [load, message]);

  const create = async () => {
    const v = await form.validateFields();
    const p = await api.createProject(v.name, v.domain);
    setCreating(false);
    form.resetFields();
    await load();
    setSelected(p.id);
  };

  const domainName = (code: string) => domains.find((d) => d.code === code)?.name ?? code;

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Layout.Sider width={240} theme="light" style={{ borderRight: "1px solid #f0f0f0" }}>
        <div style={{ padding: 16 }}>
          <Typography.Title level={5} style={{ marginTop: 0 }}>AI 설계 지원</Typography.Title>
          <Button type="primary" block onClick={() => setCreating(true)}>새 프로젝트</Button>
        </div>
        <Menu
          mode="inline"
          selectedKeys={selected ? [String(selected)] : []}
          onClick={(e) => setSelected(Number(e.key))}
          items={projects.map((p) => ({ key: String(p.id), label: `${p.name} · ${domainName(p.domain)}` }))}
        />
      </Layout.Sider>
      <Layout.Content style={{ padding: 24, background: "#fff" }}>
        {selected ? (
          <ProjectView key={selected} projectId={selected} onChanged={load} />
        ) : (
          <Empty description="프로젝트를 만들어 시작하세요" />
        )}
      </Layout.Content>
      <Modal title="새 프로젝트" open={creating} onOk={create} onCancel={() => setCreating(false)} okText="만들기">
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="프로젝트 이름" rules={[{ required: true }]}>
            <Input placeholder="예: A사 재고관리 시스템" />
          </Form.Item>
          <Form.Item name="domain" label="업무 도메인" rules={[{ required: true }]}>
            <Select options={domains.map((d) => ({ value: d.code, label: d.name }))} />
          </Form.Item>
        </Form>
      </Modal>
    </Layout>
  );
}
