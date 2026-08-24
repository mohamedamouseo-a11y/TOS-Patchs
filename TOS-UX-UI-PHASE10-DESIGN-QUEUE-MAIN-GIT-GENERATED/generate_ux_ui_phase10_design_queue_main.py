#!/usr/bin/env python3
import difflib, hashlib, subprocess, sys
from pathlib import Path

TARGET_BASE_HEAD = "23cf9cade2e57fb85bfff404a6df606c0bf2c707"
TARGET_FILE = "frontend/src/pages/DesignQueuePage.jsx"
EXPECTED_BLOB = "3a28f5cd116ad43c385ac755a4b3fd22bc01195a"

REPLACEMENTS = [
('    <div className="flex min-w-[122px] flex-1 flex-col items-center text-center">','    <div className="flex min-w-[102px] flex-1 flex-col items-center text-center">',1),
('      <div className="relative grid h-20 w-20 place-items-center rounded-full" style={{ background: `conic-gradient(${color} ${percent * 3.6}deg, #e4e4e7 0deg)` }}>','      <div className="relative grid h-16 w-16 place-items-center rounded-full" style={{ background: `conic-gradient(${color} ${percent * 3.6}deg, #e4e4e7 0deg)` }}>',1),
('        <div className="grid h-14 w-14 place-items-center rounded-full bg-white text-lg font-black text-zinc-950 shadow-inner dark:bg-zinc-950 dark:text-white">{numeric}</div>','        <div className="grid h-11 w-11 place-items-center rounded-full bg-white text-base font-black text-zinc-950 shadow-inner dark:bg-zinc-950 dark:text-white">{numeric}</div>',1),
('      <div className="mt-2 text-xs font-black text-zinc-800 dark:text-zinc-100">{label}</div>','      <div className="mt-1.5 text-[11px] font-black text-zinc-800 dark:text-zinc-100">{label}</div>',1),
('      <div className="mt-1 text-[10px] font-bold text-zinc-400">{percent}% {note}</div>','      <div className="mt-0.5 text-[9px] font-bold text-zinc-400">{percent}% {note}</div>',1),
('    <button type="button" onClick={() => onSelect(task.id)} className="w-full rounded-2xl border border-zinc-100 bg-white p-3 text-start shadow-sm transition hover:-translate-y-0.5 hover:border-amber-300 hover:shadow-md dark:border-white/10 dark:bg-zinc-950">','    <button type="button" onClick={() => onSelect(task.id)} className="w-full rounded-[16px] border border-zinc-100 bg-white p-2.5 text-start shadow-sm transition hover:-translate-y-0.5 hover:border-amber-300 hover:shadow-md dark:border-white/10 dark:bg-zinc-950">',1),
('      <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] font-bold text-zinc-500 dark:text-zinc-300">','      <div className="mt-2.5 flex flex-wrap items-center gap-1.5 text-[10px] font-bold text-zinc-500 dark:text-zinc-300">',1),
('      <div className="mt-3 flex items-center justify-between gap-2 border-t border-zinc-100 pt-2.5 dark:border-white/10">','      <div className="mt-2.5 flex items-center justify-between gap-2 border-t border-zinc-100 pt-2 dark:border-white/10">',1),
('      <div className="grid h-full min-w-[1180px] grid-cols-5 gap-3 p-3">','      <div className="grid h-full min-w-[1080px] grid-cols-5 gap-2.5 p-2.5">',1),
('            <section key={column.id} className="flex h-full min-w-0 flex-col overflow-hidden rounded-[24px] border border-zinc-100 bg-zinc-50/80 dark:border-white/10 dark:bg-white/[0.03]">','            <section key={column.id} className="flex h-full min-w-0 flex-col overflow-hidden rounded-[18px] border border-zinc-100 bg-zinc-50/80 dark:border-white/10 dark:bg-white/[0.03]">',1),
('              <div className="border-b border-zinc-100 bg-white px-3.5 py-3 dark:border-white/10 dark:bg-zinc-950"><div className="flex items-center justify-between gap-2"><div className="flex items-center gap-2"><span className={cn("h-2.5 w-2.5 rounded-full", column.accent)} /><span className="text-sm font-black text-zinc-900 dark:text-white">{column.label}</span></div><span className={cn("rounded-full px-2 py-1 text-[11px] font-black text-zinc-700 dark:text-zinc-200", column.soft)}>{tasks.length}</span></div><div className="mt-1 text-[10px] font-bold text-zinc-400">{column.hint}</div></div>','              <div className="border-b border-zinc-100 bg-white px-3 py-2.5 dark:border-white/10 dark:bg-zinc-950"><div className="flex items-center justify-between gap-2"><div className="flex items-center gap-2"><span className={cn("h-2 w-2 rounded-full", column.accent)} /><span className="text-xs font-black text-zinc-900 dark:text-white">{column.label}</span></div><span className={cn("rounded-full px-2 py-0.5 text-[10px] font-black text-zinc-700 dark:text-zinc-200", column.soft)}>{tasks.length}</span></div><div className="mt-0.5 text-[9px] font-bold text-zinc-400">{column.hint}</div></div>',1),
('              <div className="min-h-0 flex-1 space-y-2.5 overflow-y-auto p-2.5">{tasks.map((task) => <TaskCard key={task.id} task={task} onSelect={onSelectTask} capacityMode={capacityMode} tr={tr} lang={lang} />)}{!tasks.length && <div className="grid min-h-28 place-items-center rounded-2xl border border-dashed border-zinc-200 bg-white/70 px-4 text-center text-xs font-bold text-zinc-400 dark:border-white/10 dark:bg-white/[0.02]">{tr.queue.noColumnTasks}</div>}</div>','              <div className="min-h-0 flex-1 space-y-2 overflow-y-auto p-2">{tasks.map((task) => <TaskCard key={task.id} task={task} onSelect={onSelectTask} capacityMode={capacityMode} tr={tr} lang={lang} />)}{!tasks.length && <div className="grid min-h-20 place-items-center rounded-xl border border-dashed border-zinc-200 bg-white/70 px-3 text-center text-[11px] font-bold text-zinc-400 dark:border-white/10 dark:bg-white/[0.02]">{tr.queue.noColumnTasks}</div>}</div>',1),
('      <button type="button" onClick={() => setCollapsed(!collapsed)} className="flex w-full items-center justify-between gap-3 px-4 py-3 text-start">','      <button type="button" onClick={() => setCollapsed(!collapsed)} className="flex w-full items-center justify-between gap-3 px-3.5 py-2.5 text-start">',1),
('        ].map((item) => <div key={item.label} className="rounded-2xl border border-zinc-100 bg-zinc-50 px-4 py-3 dark:border-white/10 dark:bg-white/5">','        ].map((item) => <div key={item.label} className="rounded-xl border border-zinc-100 bg-zinc-50 px-3 py-2.5 dark:border-white/10 dark:bg-white/5">',1),
('        <div className="mt-4 grid gap-2 md:grid-cols-[1.3fr_.8fr_.8fr]">','        <div className="mt-3 grid gap-2 md:grid-cols-[1.3fr_.8fr_.8fr]">',1),
('          <div className="hidden grid-cols-[1.45fr_.8fr_1.1fr_.65fr_.75fr_1fr] gap-3 bg-zinc-50 px-4 py-3 text-[10px] font-black text-zinc-400 lg:grid">','          <div className="hidden grid-cols-[1.45fr_.8fr_1.1fr_.65fr_.75fr_1fr] gap-3 bg-zinc-50 px-4 py-2.5 text-[10px] font-black text-zinc-400 lg:grid">',1),
('return <div key={designer.id} className="grid gap-3 px-4 py-4 lg:grid-cols-[1.45fr_.8fr_1.1fr_.65fr_.75fr_1fr] lg:items-center">','return <div key={designer.id} className="grid gap-3 px-4 py-3 lg:grid-cols-[1.45fr_.8fr_1.1fr_.65fr_.75fr_1fr] lg:items-center">',1),
('      <div className="flex flex-wrap justify-between gap-7 px-2 py-3">','      <div className="flex flex-wrap justify-between gap-4 px-2 py-2">',1),
('      <Card className="p-3.5">','      <Card className="p-3">',1),
('        <div className="grid gap-2.5 md:grid-cols-2 xl:grid-cols-[1.3fr_1fr_1fr_1fr_1fr_auto]">','        <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-[1.3fr_1fr_1fr_1fr_1fr_auto]">',1),
('        <div className="mt-3 flex items-center gap-2 border-t border-zinc-100 pt-3 text-xs font-bold text-zinc-400 dark:border-white/10">','        <div className="mt-2.5 flex items-center gap-2 border-t border-zinc-100 pt-2.5 text-[11px] font-bold text-zinc-400 dark:border-white/10">',1),
('      <Card className="h-[calc(100vh-390px)] min-h-[610px] overflow-hidden p-0">','      <Card className="h-[calc(100vh-350px)] min-h-[640px] overflow-hidden p-0">',1),
('        <div className="flex items-center justify-between gap-3 border-b border-zinc-100 px-4 py-3 dark:border-white/10">','        <div className="flex items-center justify-between gap-3 border-b border-zinc-100 px-4 py-2.5 dark:border-white/10">',1),
('        <div className="h-[calc(100%-65px)] min-h-0"><KanbanBoard columns={kanbanColumns} onSelectTask={openTask} loading={loading} capacityMode={settings.capacityMode} tr={tr} lang={lang} /></div>','        <div className="h-[calc(100%-58px)] min-h-0"><KanbanBoard columns={kanbanColumns} onSelectTask={openTask} loading={loading} capacityMode={settings.capacityMode} tr={tr} lang={lang} /></div>',1),
]

REQUIRED_MARKERS = ['function QueueStatRing(','function TaskCard(','function KanbanBoard(','function CapacitySection(','function DetailsWorkspace(','export function DesignQueuePage(','api.tasks.designQueue(','api.tasks.designQueueDetails(','api.tasks.assignDesignQueueTask(','api.tasks.updateDesignCapacity(','api.tasks.selfAssignDesignQueueTask(','api.tasks.rejectDesignQueueTask(','api.tasks.archiveDesignQueueTask(','api.tasks.restoreDesignQueueTask(','tasksApi.uploadTaskFiles(']

def run(cmd,cwd): return subprocess.check_output(cmd,cwd=cwd,text=True).strip()
def git_blob_sha(data): return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()
def replace_exact(text,old,new,count,label):
    actual=text.count(old)
    if actual!=count: raise RuntimeError(f"ANCHOR_{label}_COUNT={actual}; expected {count}")
    return text.replace(old,new)
def details_block(text):
    a=text.find('function DetailsWorkspace('); b=text.find('export function DesignQueuePage(',a+1)
    if a<0 or b<0 or b<=a: raise RuntimeError('DESIGN_DETAILS_BLOCK_NOT_FOUND')
    return text[a:b]

def main():
    if len(sys.argv)!=3: print('Usage: generate_ux_ui_phase10_design_queue_main.py <repo> <output.patch>',file=sys.stderr); return 2
    repo=Path(sys.argv[1]).resolve(); output=Path(sys.argv[2]).resolve(); target=repo/TARGET_FILE
    branch=run(['git','branch','--show-current'],repo); head=run(['git','rev-parse','HEAD'],repo); blob=run(['git','hash-object','--',TARGET_FILE],repo)
    if branch!='main': raise RuntimeError(f'BRANCH={branch}; expected main')
    if head!=TARGET_BASE_HEAD: raise RuntimeError(f'HEAD={head}; expected {TARGET_BASE_HEAD}')
    if blob!=EXPECTED_BLOB: raise RuntimeError(f'BLOB={blob}; expected {EXPECTED_BLOB}')
    original=target.read_text(encoding='utf-8'); original_details=details_block(original); updated=original
    for idx,(old,new,count) in enumerate(REPLACEMENTS,1): updated=replace_exact(updated,old,new,count,f'{idx:02d}')
    if updated==original: raise RuntimeError('NO_CHANGES')
    if details_block(updated)!=original_details: raise RuntimeError('DESIGN_DETAILS_CHANGED')
    for marker in REQUIRED_MARKERS:
        if original.count(marker)!=updated.count(marker): raise RuntimeError(f'BEHAVIOR_MARKER_CHANGED={marker}')
    if original.count('api.')!=updated.count('api.'): raise RuntimeError('API_CALL_COUNT_CHANGED')
    if original.count('tasksApi.')!=updated.count('tasksApi.'): raise RuntimeError('TASKS_API_CALL_COUNT_CHANGED')
    for line_no,line in enumerate(updated.splitlines(),1):
        if line.rstrip()!=line: raise RuntimeError(f'TRAILING_WHITESPACE_LINE={line_no}')
    data=updated.encode(); new_blob=git_blob_sha(data)
    diff=list(difflib.unified_diff(original.splitlines(keepends=True),updated.splitlines(keepends=True),fromfile=f'a/{TARGET_FILE}',tofile=f'b/{TARGET_FILE}',n=3))
    patch=f'diff --git a/{TARGET_FILE} b/{TARGET_FILE}\nindex {EXPECTED_BLOB[:7]}..{new_blob[:7]} 100644\n'+''.join(diff)
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(patch,encoding='utf-8')
    sha=hashlib.sha256(output.read_bytes()).hexdigest()
    print(f'TARGET_BASE_HEAD={TARGET_BASE_HEAD}'); print(f'TARGET_FILE={TARGET_FILE}'); print(f'EXPECTED_BLOB={EXPECTED_BLOB}'); print(f'NEW_BLOB={new_blob}')
    print('SOURCE_SCOPE=ONE_FILE'); print('DESIGN_QUEUE_SCOPE=MAIN_QUEUE_ONLY'); print('DESIGN_DETAILS_CHANGED=NO'); print('DESIGN_BEHAVIOR_CHANGED=NO'); print('API_CALLS_CHANGED=NO'); print('TASKS_API_CALLS_CHANGED=NO'); print('ROUTES_CHANGED=NO'); print('PERMISSIONS_CHANGED=NO'); print('BACKEND_INCLUDED=NO'); print('GENERATOR_V1=YES'); print(f'REPLACEMENTS={len(REPLACEMENTS)}'); print(f'PATCH_SHA256={sha}'); print(f'PATCH_PATH={output}')
    return 0
if __name__=='__main__': raise SystemExit(main())
