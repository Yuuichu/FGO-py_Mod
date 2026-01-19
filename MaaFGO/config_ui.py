#!/usr/bin/env python3
"""
MaaFGO 配置界面

基于 interface.json 的可视化配置工具。
支持 CLI 和 简单 GUI 两种模式。

使用方法：
    python config_ui.py              # CLI 模式
    python config_ui.py --gui        # GUI 模式（需要 tkinter）
    python config_ui.py --list       # 列出所有任务
    python config_ui.py --run 自动刷本  # 直接运行指定任务
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# 配置文件路径
INTERFACE_PATH = Path(__file__).parent / "interface.json"
CONFIG_PATH = Path(__file__).parent / "config" / "user_config.json"


class MaaFGOConfig:
    """MaaFGO 配置管理器"""
    
    def __init__(self):
        self.interface = self._load_interface()
        self.user_config = self._load_user_config()
    
    def _load_interface(self) -> dict:
        """加载 interface.json"""
        if INTERFACE_PATH.exists():
            with open(INTERFACE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def _load_user_config(self) -> dict:
        """加载用户配置"""
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"selected_task": None, "options": {}}
    
    def save_user_config(self):
        """保存用户配置"""
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.user_config, f, ensure_ascii=False, indent=2)
    
    @property
    def name(self) -> str:
        return self.interface.get("name", "MaaFGO")
    
    @property
    def version(self) -> str:
        return self.interface.get("version", "0.0.0")
    
    @property
    def description(self) -> str:
        return self.interface.get("description", "")
    
    @property
    def tasks(self) -> List[dict]:
        return self.interface.get("task", [])
    
    @property
    def options(self) -> Dict[str, dict]:
        return self.interface.get("option", {})
    
    @property
    def controllers(self) -> List[dict]:
        return self.interface.get("controller", [])
    
    def get_task_by_name(self, name: str) -> Optional[dict]:
        """根据名称获取任务"""
        for task in self.tasks:
            if task.get("name") == name:
                return task
        return None
    
    def get_option_cases(self, option_name: str) -> List[dict]:
        """获取选项的所有选择"""
        option = self.options.get(option_name, {})
        return option.get("cases", [])
    
    def get_default_case(self, option_name: str) -> Optional[str]:
        """获取选项的默认值"""
        for case in self.get_option_cases(option_name):
            if case.get("default"):
                return case.get("name")
        cases = self.get_option_cases(option_name)
        return cases[0].get("name") if cases else None
    
    def set_option(self, option_name: str, case_name: str):
        """设置选项值"""
        self.user_config["options"][option_name] = case_name
    
    def get_option(self, option_name: str) -> str:
        """获取选项当前值"""
        return self.user_config["options"].get(
            option_name, 
            self.get_default_case(option_name)
        )
    
    def set_task(self, task_name: str):
        """设置当前任务"""
        self.user_config["selected_task"] = task_name
    
    def get_current_task(self) -> Optional[str]:
        """获取当前任务"""
        return self.user_config.get("selected_task")
    
    def build_task_config(self, task_name: str) -> dict:
        """构建任务的完整配置"""
        task = self.get_task_by_name(task_name)
        if not task:
            return {}
        
        config = {
            "entry": task.get("entry"),
            "pipeline_override": {}
        }
        
        # 合并选项的 pipeline_override
        task_options = task.get("option", [])
        for option_name in task_options:
            case_name = self.get_option(option_name)
            for case in self.get_option_cases(option_name):
                if case.get("name") == case_name:
                    override = case.get("pipeline_override", {})
                    config["pipeline_override"].update(override)
                    break
        
        return config


class CLIInterface:
    """命令行配置界面"""
    
    def __init__(self, config: MaaFGOConfig):
        self.config = config
    
    def print_header(self):
        print("=" * 60)
        print(f"  {self.config.name} v{self.config.version}")
        print(f"  {self.config.description}")
        print("=" * 60)
    
    def list_tasks(self):
        """列出所有任务"""
        print("\n可用任务:")
        for i, task in enumerate(self.config.tasks, 1):
            name = task.get("name", "Unknown")
            entry = task.get("entry", "")
            options = task.get("option", [])
            print(f"  {i}. {name}")
            print(f"     入口: {entry}")
            if options:
                print(f"     选项: {', '.join(options)}")
    
    def list_options(self, task_name: str = None):
        """列出选项"""
        print("\n配置选项:")
        
        # 如果指定了任务，只显示该任务的选项
        if task_name:
            task = self.config.get_task_by_name(task_name)
            if task:
                option_names = task.get("option", [])
            else:
                option_names = list(self.config.options.keys())
        else:
            option_names = list(self.config.options.keys())
        
        for option_name in option_names:
            current = self.config.get_option(option_name)
            cases = self.config.get_option_cases(option_name)
            case_names = [c.get("name") for c in cases]
            
            print(f"\n  {option_name}:")
            for i, case_name in enumerate(case_names, 1):
                marker = "→" if case_name == current else " "
                print(f"    {marker} {i}. {case_name}")
    
    def select_task(self) -> Optional[str]:
        """选择任务"""
        self.list_tasks()
        
        try:
            choice = input("\n请选择任务 (输入编号或名称): ").strip()
            
            # 尝试作为编号
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self.config.tasks):
                    return self.config.tasks[idx].get("name")
            except ValueError:
                pass
            
            # 尝试作为名称
            for task in self.config.tasks:
                if task.get("name") == choice:
                    return task.get("name")
            
            print("无效选择")
            return None
            
        except KeyboardInterrupt:
            print("\n取消")
            return None
    
    def configure_options(self, task_name: str):
        """配置任务选项"""
        task = self.config.get_task_by_name(task_name)
        if not task:
            return
        
        option_names = task.get("option", [])
        if not option_names:
            print("该任务没有可配置的选项")
            return
        
        print(f"\n配置任务: {task_name}")
        
        for option_name in option_names:
            cases = self.config.get_option_cases(option_name)
            current = self.config.get_option(option_name)
            
            print(f"\n{option_name} (当前: {current}):")
            for i, case in enumerate(cases, 1):
                name = case.get("name")
                marker = "*" if name == current else " "
                print(f"  {marker}{i}. {name}")
            
            try:
                choice = input("选择 (回车保持当前): ").strip()
                if choice:
                    try:
                        idx = int(choice) - 1
                        if 0 <= idx < len(cases):
                            self.config.set_option(option_name, cases[idx].get("name"))
                            print(f"  已设置为: {cases[idx].get('name')}")
                    except ValueError:
                        print("  无效输入，保持当前值")
            except KeyboardInterrupt:
                print("\n跳过")
        
        self.config.save_user_config()
        print("\n配置已保存")
    
    def run_interactive(self):
        """交互式配置"""
        self.print_header()
        
        while True:
            print("\n操作:")
            print("  1. 选择任务")
            print("  2. 配置选项")
            print("  3. 运行任务")
            print("  4. 查看当前配置")
            print("  0. 退出")
            
            try:
                choice = input("\n请选择: ").strip()
                
                if choice == "1":
                    task_name = self.select_task()
                    if task_name:
                        self.config.set_task(task_name)
                        print(f"\n已选择任务: {task_name}")
                        
                        # 询问是否配置选项
                        task = self.config.get_task_by_name(task_name)
                        if task and task.get("option"):
                            if input("是否配置选项? (y/N): ").strip().lower() == "y":
                                self.configure_options(task_name)
                
                elif choice == "2":
                    current_task = self.config.get_current_task()
                    if current_task:
                        self.configure_options(current_task)
                    else:
                        print("请先选择任务")
                
                elif choice == "3":
                    current_task = self.config.get_current_task()
                    if current_task:
                        self.run_task(current_task)
                    else:
                        print("请先选择任务")
                
                elif choice == "4":
                    self.show_current_config()
                
                elif choice == "0":
                    print("再见!")
                    break
                
                else:
                    print("无效选择")
                    
            except KeyboardInterrupt:
                print("\n再见!")
                break
    
    def show_current_config(self):
        """显示当前配置"""
        print("\n当前配置:")
        
        task_name = self.config.get_current_task()
        if task_name:
            print(f"  任务: {task_name}")
            task = self.config.get_task_by_name(task_name)
            if task:
                print(f"  入口: {task.get('entry')}")
                
                options = task.get("option", [])
                if options:
                    print("  选项:")
                    for option_name in options:
                        value = self.config.get_option(option_name)
                        print(f"    {option_name}: {value}")
        else:
            print("  未选择任务")
    
    def run_task(self, task_name: str):
        """运行任务"""
        print(f"\n准备运行任务: {task_name}")
        
        config = self.config.build_task_config(task_name)
        print(f"入口: {config.get('entry')}")
        
        print("\n开始运行...")
        
        # 调用运行器
        try:
            from run_with_maa import MaaFGORunner
            
            runner = MaaFGORunner()
            
            if not runner.connect():
                print("连接设备失败")
                return
            
            if not runner.load_resources():
                print("加载资源失败")
                return
            
            if not runner.init_tasker():
                print("初始化失败")
                return
            
            entry = config.get("entry")
            if runner.run_task(entry):
                print("任务完成!")
            else:
                print("任务失败")
                
        except ImportError as e:
            print(f"无法导入运行器: {e}")
        except Exception as e:
            print(f"运行出错: {e}")


def create_gui():
    """创建 GUI 界面"""
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
    except ImportError:
        print("GUI 模式需要 tkinter")
        return None
    
    config = MaaFGOConfig()
    
    class MaaFGOGUI:
        def __init__(self, root):
            self.root = root
            self.root.title(f"{config.name} v{config.version}")
            self.root.geometry("600x500")
            
            self.create_widgets()
        
        def create_widgets(self):
            # 标题
            title = ttk.Label(
                self.root, 
                text=config.name,
                font=("", 16, "bold")
            )
            title.pack(pady=10)
            
            desc = ttk.Label(self.root, text=config.description)
            desc.pack()
            
            # 任务选择
            task_frame = ttk.LabelFrame(self.root, text="任务选择", padding=10)
            task_frame.pack(fill="x", padx=10, pady=5)
            
            self.task_var = tk.StringVar()
            task_names = [t.get("name") for t in config.tasks]
            task_combo = ttk.Combobox(
                task_frame, 
                textvariable=self.task_var,
                values=task_names,
                state="readonly",
                width=40
            )
            task_combo.pack(side="left", padx=5)
            task_combo.bind("<<ComboboxSelected>>", self.on_task_selected)
            
            # 选项区域
            self.options_frame = ttk.LabelFrame(self.root, text="配置选项", padding=10)
            self.options_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            self.option_vars = {}
            
            # 按钮区域
            btn_frame = ttk.Frame(self.root)
            btn_frame.pack(fill="x", padx=10, pady=10)
            
            ttk.Button(btn_frame, text="保存配置", command=self.save_config).pack(side="left", padx=5)
            ttk.Button(btn_frame, text="运行任务", command=self.run_task).pack(side="left", padx=5)
            ttk.Button(btn_frame, text="退出", command=self.root.quit).pack(side="right", padx=5)
            
            # 状态栏
            self.status_var = tk.StringVar(value="就绪")
            status = ttk.Label(self.root, textvariable=self.status_var, relief="sunken")
            status.pack(fill="x", side="bottom")
            
            # 加载当前配置
            current_task = config.get_current_task()
            if current_task:
                self.task_var.set(current_task)
                self.on_task_selected(None)
        
        def on_task_selected(self, event):
            """任务选择变化"""
            task_name = self.task_var.get()
            task = config.get_task_by_name(task_name)
            
            # 清空选项区域
            for widget in self.options_frame.winfo_children():
                widget.destroy()
            self.option_vars.clear()
            
            if not task:
                return
            
            # 创建选项控件
            options = task.get("option", [])
            for i, option_name in enumerate(options):
                row = ttk.Frame(self.options_frame)
                row.pack(fill="x", pady=2)
                
                ttk.Label(row, text=f"{option_name}:", width=15).pack(side="left")
                
                var = tk.StringVar(value=config.get_option(option_name))
                self.option_vars[option_name] = var
                
                cases = config.get_option_cases(option_name)
                case_names = [c.get("name") for c in cases]
                
                combo = ttk.Combobox(
                    row,
                    textvariable=var,
                    values=case_names,
                    state="readonly",
                    width=30
                )
                combo.pack(side="left", padx=5)
        
        def save_config(self):
            """保存配置"""
            task_name = self.task_var.get()
            if task_name:
                config.set_task(task_name)
            
            for option_name, var in self.option_vars.items():
                config.set_option(option_name, var.get())
            
            config.save_user_config()
            self.status_var.set("配置已保存")
            messagebox.showinfo("保存", "配置已保存")
        
        def run_task(self):
            """运行任务"""
            task_name = self.task_var.get()
            if not task_name:
                messagebox.showwarning("警告", "请先选择任务")
                return
            
            self.save_config()
            self.status_var.set(f"正在运行: {task_name}")
            
            # 在新线程中运行
            import threading
            thread = threading.Thread(target=self._run_task_thread, args=(task_name,))
            thread.start()
        
        def _run_task_thread(self, task_name):
            try:
                from run_with_maa import MaaFGORunner
                
                runner = MaaFGORunner()
                
                if not runner.connect():
                    self.root.after(0, lambda: messagebox.showerror("错误", "连接设备失败"))
                    return
                
                if not runner.load_resources():
                    self.root.after(0, lambda: messagebox.showerror("错误", "加载资源失败"))
                    return
                
                if not runner.init_tasker():
                    self.root.after(0, lambda: messagebox.showerror("错误", "初始化失败"))
                    return
                
                task_config = config.build_task_config(task_name)
                entry = task_config.get("entry")
                
                if runner.run_task(entry):
                    self.root.after(0, lambda: messagebox.showinfo("完成", "任务完成!"))
                else:
                    self.root.after(0, lambda: messagebox.showwarning("警告", "任务失败"))
                    
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", str(e)))
            finally:
                self.root.after(0, lambda: self.status_var.set("就绪"))
    
    root = tk.Tk()
    app = MaaFGOGUI(root)
    return root


def main():
    parser = argparse.ArgumentParser(description="MaaFGO 配置界面")
    parser.add_argument("--gui", "-g", action="store_true", help="使用 GUI 模式")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有任务")
    parser.add_argument("--run", "-r", help="直接运行指定任务")
    parser.add_argument("--config", "-c", help="配置指定任务")
    
    args = parser.parse_args()
    
    config = MaaFGOConfig()
    cli = CLIInterface(config)
    
    if args.list:
        cli.print_header()
        cli.list_tasks()
        cli.list_options()
        return 0
    
    if args.run:
        cli.print_header()
        cli.run_task(args.run)
        return 0
    
    if args.config:
        cli.print_header()
        cli.configure_options(args.config)
        return 0
    
    if args.gui:
        root = create_gui()
        if root:
            root.mainloop()
        return 0
    
    # 默认：交互式 CLI
    cli.run_interactive()
    return 0


if __name__ == "__main__":
    sys.exit(main())
