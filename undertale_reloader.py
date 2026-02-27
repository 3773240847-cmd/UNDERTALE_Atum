#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Undertale 重启工具 - 存档管理版
F1 - 极速重启游戏
F2 - 清除存档并重启
F6 - 重启游戏并解压存档
"""

import os
import sys
import time
import subprocess
import zipfile
import shutil
import glob
from datetime import datetime
from functools import lru_cache

# 尝试导入必要的库
try:
    from keyboard import add_hotkey, wait
except ImportError:
    print("="*50)
    print("错误：缺少 keyboard 库")
    print("="*50)
    print("请运行：pip install keyboard psutil")
    input("\n按回车键退出...")
    sys.exit(1)

try:
    from psutil import process_iter, NoSuchProcess, AccessDenied
except ImportError:
    print("="*50)
    print("错误：缺少 psutil 库")
    print("="*50)
    print("请运行：pip install psutil")
    input("\n按回车键退出...")
    sys.exit(1)


class UndertaleReloader:
    """Undertale重启管理类"""
    
    def __init__(self):
        """初始化"""
        # 游戏相关路径
        self.program_name = "undertale.exe"
        self.program_path = r"E:\UNDERTALE_V1.001_Linux\UNDERTALE.exe"
        self.game_dir = r"E:\UNDERTALE_V1.001_Linux"
        
        # 存档相关路径
        self.archive_path = r"C:\Users\Administrator\AppData\Local\UNDERTALE_linux_steamver\SAPC.zip"
        
        # 游戏存档文件（完整列表）
        self.save_files = [
            # 主要存档文件
            "file0",      # 主存档槽1
            "file8",      # 主存档槽2
            "file9",      # 主存档槽3
            
            # 系统文件
            "system_information_962",  # 系统信息1
            "system_information_963",  # 系统信息2
            
            # 配置文件
            "undertale.ini",           # 主配置文件
            "config.ini",              # 配置文件
            
            # 成就文件
            "playerachievementcache.dat",  # 玩家成就缓存
            
            # 其他可能文件
            "save",                    # 存档目录
        ]
        
        # 缓存
        self._path_cache = {}
        self._process_cache = []
        self._last_process_check = 0
        self._process_cache_duration = 0.5
        
        # 快速检查路径
        self._quick_check_paths()
    
    def _quick_check_paths(self):
        """快速路径检查"""
        print("\n" + "="*60)
        print("Undertale 重启工具 (存档管理版)")
        print("="*60)
        
        # 检查游戏程序
        if os.path.exists(self.program_path):
            print(f"✓ 游戏程序：{self.program_path}")
        else:
            print(f"✗ 游戏程序不存在：{self.program_path}")
            print("  请检查路径是否正确")
        
        # 检查游戏目录
        if os.path.exists(self.game_dir):
            print(f"✓ 游戏目录：{self.game_dir}")
        else:
            print(f"✗ 游戏目录不存在：{self.game_dir}")
        
        # 检查存档文件
        if os.path.exists(self.archive_path):
            archive_size = os.path.getsize(self.archive_path) / 1024
            print(f"✓ 存档文件：{self.archive_path} ({archive_size:.1f} KB)")
        else:
            print(f"✗ 存档文件不存在：{self.archive_path}")
            print("  请检查存档路径是否正确")
        
        print("="*60)
    
    @lru_cache(maxsize=32)
    def _path_exists(self, path):
        """缓存路径检查"""
        return os.path.exists(path)
    
    def find_undertale_processes_fast(self):
        """快速查找Undertale进程"""
        current_time = time.time()
        
        # 如果缓存还在有效期内，直接返回缓存
        if current_time - self._last_process_check < self._process_cache_duration:
            return self._process_cache
        
        # 更新缓存
        processes = []
        try:
            for proc in process_iter(['name', 'pid']):
                try:
                    if proc.info['name'] and proc.info['name'].lower() == self.program_name:
                        processes.append(proc)
                except (NoSuchProcess, AccessDenied):
                    pass
        except Exception:
            pass
        
        self._process_cache = processes
        self._last_process_check = current_time
        return processes
    
    def close_undertale_fast(self):
        """快速关闭Undertale"""
        processes = self.find_undertale_processes_fast()
        
        if not processes:
            return False
        
        # 使用taskkill快速关闭（Windows最快的方法）
        if os.name == 'nt':
            try:
                subprocess.run(['taskkill', '/f', '/im', self.program_name], 
                             capture_output=True, timeout=1)
                self._last_process_check = 0
                return True
            except:
                pass
        
        # 如果taskkill失败，使用常规方法
        for proc in processes:
            try:
                proc.kill()
            except:
                pass
        
        self._last_process_check = 0
        return True
    
    def clear_save_files(self):
        """清除游戏目录中的所有存档文件"""
        self.log("开始清除存档文件...")
        
        if not os.path.exists(self.game_dir):
            self.log(f"错误：游戏目录不存在 - {self.game_dir}")
            return False
        
        deleted_files = []
        
        # 1. 删除指定的存档文件
        for filename in self.save_files:
            file_path = os.path.join(self.game_dir, filename)
            
            # 检查是否是目录
            if os.path.isdir(file_path):
                try:
                    shutil.rmtree(file_path)
                    deleted_files.append(filename + "/")
                    self.log(f"已删除目录: {filename}")
                except Exception as e:
                    self.log(f"删除目录失败 {filename}: {e}")
            
            # 检查是否是文件
            elif os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    deleted_files.append(filename)
                    self.log(f"已删除: {filename}")
                except Exception as e:
                    self.log(f"删除失败 {filename}: {e}")
        
        # 2. 删除所有 file 开头的文件 (file0, file1, file2, ...)
        file_pattern = os.path.join(self.game_dir, "file*")
        for match_file in glob.glob(file_pattern):
            if os.path.isfile(match_file):
                try:
                    os.remove(match_file)
                    base_name = os.path.basename(match_file)
                    if base_name not in deleted_files:
                        deleted_files.append(base_name)
                        self.log(f"已删除: {base_name}")
                except Exception as e:
                    self.log(f"删除失败 {match_file}: {e}")
        
        # 3. 删除所有 system_information 开头的文件
        sys_pattern = os.path.join(self.game_dir, "system_information*")
        for match_file in glob.glob(sys_pattern):
            if os.path.isfile(match_file):
                try:
                    os.remove(match_file)
                    base_name = os.path.basename(match_file)
                    if base_name not in deleted_files:
                        deleted_files.append(base_name)
                        self.log(f"已删除: {base_name}")
                except Exception as e:
                    self.log(f"删除失败 {match_file}: {e}")
        
        # 4. 删除所有 .dat 文件（成就缓存）
        dat_files = glob.glob(os.path.join(self.game_dir, "*.dat"))
        for dat_file in dat_files:
            try:
                os.remove(dat_file)
                base_name = os.path.basename(dat_file)
                if base_name not in deleted_files:
                    deleted_files.append(base_name)
                    self.log(f"已删除: {base_name}")
            except Exception as e:
                self.log(f"删除失败 {dat_file}: {e}")
        
        # 5. 删除所有 .ini 文件（配置文件）
        ini_files = glob.glob(os.path.join(self.game_dir, "*.ini"))
        for ini_file in ini_files:
            try:
                os.remove(ini_file)
                base_name = os.path.basename(ini_file)
                if base_name not in deleted_files:
                    deleted_files.append(base_name)
                    self.log(f"已删除: {base_name}")
            except Exception as e:
                self.log(f"删除失败 {ini_file}: {e}")
        
        self.log(f"清除完成: 删除 {len(deleted_files)} 个文件")
        return len(deleted_files) > 0
    
    def extract_archive_fast(self, clear_first=False):
        """快速解压存档（可选择是否先清除）"""
        # 检查存档文件
        if not self._path_exists(self.archive_path):
            self.log("错误：存档文件不存在")
            return False
        
        if not self._path_exists(self.game_dir):
            self.log("错误：游戏目录不存在")
            return False
        
        try:
            # 如果需要，先清除现有存档
            if clear_first:
                self.clear_save_files()
                time.sleep(0.1)  # 极短等待
            
            # 解压新存档
            self.log(f"正在解压存档: {self.archive_path}")
            
            with zipfile.ZipFile(self.archive_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                self.log(f"存档包含 {len(file_list)} 个文件")
                
                # 解压到游戏目录
                zip_ref.extractall(self.game_dir)
            
            # 验证解压的文件
            extracted_count = 0
            for file in file_list[:3]:  # 只验证前3个
                file_path = os.path.join(self.game_dir, file)
                if os.path.exists(file_path):
                    extracted_count += 1
            
            if extracted_count > 0:
                self.log(f"✓ 成功解压 {len(file_list)} 个文件")
                return True
            else:
                self.log("⚠ 解压可能失败")
                return False
                
        except zipfile.BadZipFile:
            self.log("错误：存档文件损坏")
            return False
        except Exception as e:
            self.log(f"解压出错: {e}")
            return False
    
    def start_undertale_fast(self):
        """快速启动Undertale"""
        if not self._path_exists(self.program_path):
            self.log("错误：找不到游戏程序")
            return False
        
        try:
            if os.name == 'nt':
                os.startfile(self.program_path)
            else:
                subprocess.Popen([self.program_path], cwd=self.game_dir)
            return True
        except Exception as e:
            self.log(f"启动失败: {e}")
            return False
    
    def log(self, message):
        """简洁日志"""
        print(f"  {message}")
    
    def quick_reload(self):
        """F1 - 极速重启"""
        print("\n" + "="*60)
        print("F1: 极速重启")
        print("="*60)
        
        # 关闭游戏
        if self.close_undertale_fast():
            print("  ✓ 游戏已关闭")
        else:
            print("  - 游戏未运行")
        
        # 立即启动
        time.sleep(0.1)
        if self.start_undertale_fast():
            print("  ✓ 游戏已启动")
        
        print("="*60)
        print("重启完成！")
        print("="*60)
    
    def clear_and_reload(self):
        """F2 - 清除存档并重启"""
        print("\n" + "="*60)
        print("F2: 清除存档并重启")
        print("="*60)
        
        # 关闭游戏
        if self.close_undertale_fast():
            print("  ✓ 游戏已关闭")
        else:
            print("  - 游戏未运行")
        
        time.sleep(0.2)
        
        # 清除存档
        print("  - 正在清除存档...")
        if self.clear_save_files():
            print("  ✓ 存档已清除")
        else:
            print("  - 没有找到存档文件")
        
        time.sleep(0.1)
        
        # 启动游戏
        if self.start_undertale_fast():
            print("  ✓ 游戏已启动")
        
        print("="*60)
        print("存档清除完成，游戏已重启！")
        print("="*60)
    
    def reload_with_archive(self):
        """F6 - 重启并解压存档（先清除后解压）"""
        print("\n" + "="*60)
        print("F6: 更新存档并重启")
        print("="*60)
        
        # 关闭游戏
        if self.close_undertale_fast():
            print("  ✓ 游戏已关闭")
        else:
            print("  - 游戏未运行")
        
        time.sleep(0.2)
        
        # 清除旧存档并解压新存档
        print("  - 正在更新存档...")
        if self.extract_archive_fast(clear_first=True):
            print("  ✓ 存档已更新")
        else:
            print("  ⚠ 存档更新失败")
        
        time.sleep(0.1)
        
        # 启动游戏
        if self.start_undertale_fast():
            print("  ✓ 游戏已启动")
        
        print("="*60)
        print("存档更新完成，游戏已重启！")
        print("="*60)
    
    def check_status_fast(self):
        """快速检查状态"""
        print("\n" + "="*60)
        print("Undertale 状态")
        print("="*60)
        
        # 检查游戏进程
        processes = self.find_undertale_processes_fast()
        if processes:
            print(f"  ✓ 游戏运行中 ({len(processes)} 进程)")
        else:
            print(f"  ✗ 游戏未运行")
        
        # 检查存档文件
        save_files_found = []
        for pattern in ["file*", "system_information*", "*.dat", "*.ini"]:
            for file_path in glob.glob(os.path.join(self.game_dir, pattern)):
                if os.path.isfile(file_path):
                    save_files_found.append(os.path.basename(file_path))
        
        if save_files_found:
            print(f"  ✓ 游戏目录中有 {len(save_files_found)} 个存档文件")
            # 只显示前5个
            for f in sorted(save_files_found)[:5]:
                file_path = os.path.join(self.game_dir, f)
                size = os.path.getsize(file_path) / 1024
                print(f"    └ {f} ({size:.1f} KB)")
            if len(save_files_found) > 5:
                print(f"    └ ... 等 {len(save_files_found)} 个文件")
        else:
            print(f"  ✗ 游戏目录中无存档文件")
        
        # 检查存档包
        if os.path.exists(self.archive_path):
            size = os.path.getsize(self.archive_path) / 1024
            mtime = datetime.fromtimestamp(os.path.getmtime(self.archive_path))
            print(f"  ✓ 存档包存在 ({size:.1f} KB)")
            print(f"    └ 修改时间: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"  ✗ 存档包不存在")
        
        print("="*60)
    
    def test_mode(self):
        """测试模式 - 检查所有功能"""
        print("\n" + "="*60)
        print("测试模式")
        print("="*60)
        
        print("\n1. 检查游戏程序:")
        print(f"   路径: {self.program_path}")
        print(f"   存在: {os.path.exists(self.program_path)}")
        
        print("\n2. 检查游戏目录:")
        print(f"   路径: {self.game_dir}")
        print(f"   存在: {os.path.exists(self.game_dir)}")
        if os.path.exists(self.game_dir):
            print(f"   可写: {os.access(self.game_dir, os.W_OK)}")
        
        print("\n3. 检查存档文件:")
        found_count = 0
        for pattern in ["file*", "system_information*", "*.dat", "*.ini"]:
            for file_path in glob.glob(os.path.join(self.game_dir, pattern)):
                if os.path.isfile(file_path):
                    found_count += 1
                    size = os.path.getsize(file_path) / 1024
                    print(f"   ✓ {os.path.basename(file_path)} ({size:.1f} KB)")
        
        if found_count == 0:
            print("   没有找到存档文件")
        
        print("\n4. 检查存档包:")
        print(f"   路径: {self.archive_path}")
        if os.path.exists(self.archive_path):
            size = os.path.getsize(self.archive_path) / 1024
            print(f"   存在: ✓ ({size:.1f} KB)")
        else:
            print(f"   存在: ✗")
        
        print("\n5. 测试热键:")
        print("   F1 - 极速重启")
        print("   F2 - 清除存档并重启")
        print("   F6 - 更新存档并重启")
        print("   F7 - 检查状态")
        print("   F8 - 测试模式")
        print("   Esc - 退出")
        
        print("="*60)


def main():
    """主函数"""
    print("="*60)
    print("Undertale 存档管理工具 v2.0")
    print("="*60)
    print("\n热键功能：")
    print("  F1 - 极速重启 (0.5秒)")
    print("  F2 - 清除存档并重启")
    print("  F6 - 更新存档并重启")
    print("  F7 - 快速状态")
    print("  F8 - 测试模式")
    print("  Esc - 退出")
    print("="*60)
    print("\n清除的存档文件包括：")
    print("  • file0, file8, file9")
    print("  • system_information_962/963")
    print("  • playerachievementcache.dat")
    print("  • 所有 .dat 和 .ini 文件")
    print("  • 所有 file* 和 system_information* 文件")
    print("="*60)
    
    # 创建实例
    reloader = UndertaleReloader()
    
    # 注册热键
    try:
        add_hotkey('f1', reloader.quick_reload)
        add_hotkey('f2', reloader.clear_and_reload)
        add_hotkey('f6', reloader.reload_with_archive)
        add_hotkey('f7', reloader.check_status_fast)
        add_hotkey('f8', reloader.test_mode)
        add_hotkey('esc', lambda: sys.exit(0))
        print("\n✓ 热键注册成功")
    except Exception as e:
        print(f"\n✗ 热键注册失败: {e}")
        print("请以管理员身份运行")
        input("按回车键退出...")
        return
    
    print("\n等待按键... (按Esc退出)")
    
    # 保持运行
    try:
        wait()
    except KeyboardInterrupt:
        print("\n\n再见！")


if __name__ == "__main__":
    main()
