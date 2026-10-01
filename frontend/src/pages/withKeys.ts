// 편집 중인 행은 객체가 매번 바뀌므로 위치를 key 로 쓴다 (입력 포커스 유지)
export const withKeys = <T,>(rows: T[]) => rows.map((r, i) => ({ ...r, key: i }));
