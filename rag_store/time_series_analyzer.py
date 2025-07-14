"""
時間序列追蹤與分析系統
支援家庭數據的時間序列分析、趨勢追蹤、警報功能

主要功能：
1. 數據提取與儲存
2. 趨勢分析與預測
3. 變化監控與警報
4. 視覺化圖表生成
"""

import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import statistics
import re
from dataclasses import dataclass

import mysql.connector
from mysql.connector import Error
import pandas as pd
import numpy as np

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TimeSeriesDataPoint:
    """時間序列數據點"""
    date: date
    value: float
    family_member: Optional[str] = None
    document_id: Optional[int] = None
    confidence: float = 1.0
    notes: Optional[str] = None

@dataclass
class TrendAnalysis:
    """趨勢分析結果"""
    trend_type: str  # 'increasing', 'decreasing', 'stable'
    slope: float
    correlation: float
    confidence: float
    period_days: int
    change_percentage: float

@dataclass
class ForecastResult:
    """預測結果"""
    predicted_value: float
    confidence_interval: Tuple[float, float]
    prediction_date: date
    method: str

class TimeSeriesAnalyzer:
    """時間序列分析器"""
    
    def __init__(self, connection):
        self.connection = connection
        
    def extract_numeric_values(self, text: str) -> List[Dict[str, Any]]:
        """從文字中提取數值資料"""
        extracted_data = []
        
        # 體重提取（公斤）
        weight_patterns = [
            r'體重[：:\s]*(\d+(?:\.\d+)?)\s*(?:kg|公斤|KG)',
            r'重量[：:\s]*(\d+(?:\.\d+)?)\s*(?:kg|公斤|KG)',
            r'(?:體重|重量)\D*?(\d+(?:\.\d+)?)\s*(?:kg|公斤|KG)',
        ]
        
        # 身高提取（公分）
        height_patterns = [
            r'身高[：:\s]*(\d+(?:\.\d+)?)\s*(?:cm|公分|CM)',
            r'高度[：:\s]*(\d+(?:\.\d+)?)\s*(?:cm|公分|CM)',
            r'(?:身高|高度)\D*?(\d+(?:\.\d+)?)\s*(?:cm|公分|CM)',
        ]
        
        # 血壓提取
        bp_patterns = [
            r'血壓[：:\s]*(\d+)/(\d+)',
            r'BP[：:\s]*(\d+)/(\d+)',
            r'收縮壓[：:\s]*(\d+).*?舒張壓[：:\s]*(\d+)',
        ]
        
        # 成績提取
        score_patterns = [
            r'(?:國文|中文)[：:\s]*(\d+(?:\.\d+)?)\s*分',
            r'(?:數學|Math)[：:\s]*(\d+(?:\.\d+)?)\s*分',
            r'(?:英文|English)[：:\s]*(\d+(?:\.\d+)?)\s*分',
            r'(?:總平均|平均)[：:\s]*(\d+(?:\.\d+)?)\s*分',
            r'GPA[：:\s]*(\d+(?:\.\d+)?)',
        ]
        
        # 金額提取（更精確的模式）
        amount_patterns = [
            r'(?:支出|花費|費用)[：:\s]*(?:NT\$|￥|＄|元)?\s*([0-9,]+(?:\.\d+)?)\s*(?:元|塊)?',
            r'(?:收入|薪水|薪資)[：:\s]*(?:NT\$|￥|＄|元)?\s*([0-9,]+(?:\.\d+)?)\s*(?:元|塊)?',
            r'(?:總計|合計|小計)[：:\s]*(?:NT\$|￥|＄|元)?\s*([0-9,]+(?:\.\d+)?)\s*(?:元|塊)?',
        ]
        
        # 執行提取
        for pattern in weight_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = float(match.group(1))
                if 30 <= value <= 200:  # 合理體重範圍
                    extracted_data.append({
                        'type': '體重',
                        'value': value,
                        'unit': 'kg',
                        'confidence': 0.9
                    })
        
        for pattern in height_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = float(match.group(1))
                if 100 <= value <= 250:  # 合理身高範圍
                    extracted_data.append({
                        'type': '身高',
                        'value': value,
                        'unit': 'cm',
                        'confidence': 0.9
                    })
        
        for pattern in bp_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                systolic = int(match.group(1))
                diastolic = int(match.group(2))
                if 70 <= systolic <= 200 and 40 <= diastolic <= 120:
                    extracted_data.append({
                        'type': '血壓收縮壓',
                        'value': systolic,
                        'unit': 'mmHg',
                        'confidence': 0.9
                    })
                    extracted_data.append({
                        'type': '血壓舒張壓',
                        'value': diastolic,
                        'unit': 'mmHg',
                        'confidence': 0.9
                    })
        
        return extracted_data
    
    def store_time_series_data(self, series_type_name: str, value: float, 
                             data_date: date, family_member_id: Optional[int] = None,
                             document_id: Optional[int] = None, 
                             confidence: float = 1.0, notes: Optional[str] = None) -> bool:
        """儲存時間序列數據"""
        try:
            cursor = self.connection.cursor()
            
            # 取得系列類型ID
            cursor.execute("SELECT id FROM time_series_types WHERE name = %s", (series_type_name,))
            result = cursor.fetchone()
            if not result:
                logger.warning(f"時間序列類型 '{series_type_name}' 不存在")
                return False
            
            series_type_id = result[0]
            
            # 插入或更新數據
            sql = """
            INSERT INTO time_series_data 
            (series_type_id, family_member_id, document_id, data_date, value, confidence_score, notes, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'document')
            ON DUPLICATE KEY UPDATE
            value = VALUES(value),
            confidence_score = VALUES(confidence_score),
            notes = VALUES(notes),
            updated_at = CURRENT_TIMESTAMP
            """
            
            cursor.execute(sql, (series_type_id, family_member_id, document_id, 
                               data_date, value, confidence, notes))
            self.connection.commit()
            
            logger.info(f"成功儲存時間序列數據: {series_type_name} = {value} ({data_date})")
            return True
            
        except Error as e:
            logger.error(f"儲存時間序列數據失敗: {e}")
            self.connection.rollback()
            return False
    
    def get_time_series_data(self, series_type_name: str, 
                           family_member_id: Optional[int] = None,
                           start_date: Optional[date] = None,
                           end_date: Optional[date] = None,
                           limit: int = 100) -> List[TimeSeriesDataPoint]:
        """取得時間序列數據"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            sql = """
            SELECT tsd.*, tst.name as series_name, tst.unit, fm.name as family_member_name
            FROM time_series_data tsd
            JOIN time_series_types tst ON tsd.series_type_id = tst.id
            LEFT JOIN family_members fm ON tsd.family_member_id = fm.id
            WHERE tst.name = %s
            """
            params = [series_type_name]
            
            if family_member_id:
                sql += " AND tsd.family_member_id = %s"
                params.append(family_member_id)
            
            if start_date:
                sql += " AND tsd.data_date >= %s"
                params.append(start_date)
            
            if end_date:
                sql += " AND tsd.data_date <= %s"
                params.append(end_date)
            
            sql += " ORDER BY tsd.data_date ASC LIMIT %s"
            params.append(limit)
            
            cursor.execute(sql, params)
            results = cursor.fetchall()
            
            data_points = []
            for row in results:
                data_points.append(TimeSeriesDataPoint(
                    date=row['data_date'],
                    value=float(row['value']),
                    family_member=row['family_member_name'],
                    document_id=row['document_id'],
                    confidence=float(row['confidence_score']) if row['confidence_score'] else 1.0,
                    notes=row['notes']
                ))
            
            return data_points
            
        except Error as e:
            logger.error(f"取得時間序列數據失敗: {e}")
            return []
    
    def analyze_trend(self, data_points: List[TimeSeriesDataPoint], 
                     period_days: int = 30) -> TrendAnalysis:
        """分析趨勢"""
        if len(data_points) < 2:
            return TrendAnalysis('stable', 0, 0, 0, 0, 0)
        
        # 準備數據
        dates = [(point.date - data_points[0].date).days for point in data_points]
        values = [point.value for point in data_points]
        
        # 計算線性回歸
        n = len(data_points)
        x_mean = statistics.mean(dates)
        y_mean = statistics.mean(values)
        
        # 計算斜率和相關係數
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(dates, values))
        x_variance = sum((x - x_mean) ** 2 for x in dates)
        y_variance = sum((y - y_mean) ** 2 for y in values)
        
        if x_variance == 0:
            slope = 0
            correlation = 0
        else:
            slope = numerator / x_variance
            correlation = numerator / (x_variance * y_variance) ** 0.5 if y_variance > 0 else 0
        
        # 判斷趨勢類型
        if abs(slope) < 0.01:
            trend_type = 'stable'
        elif slope > 0:
            trend_type = 'increasing'
        else:
            trend_type = 'decreasing'
        
        # 計算變化百分比
        if len(values) >= 2:
            change_percentage = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
        else:
            change_percentage = 0
        
        # 計算信心度（基於R²）
        confidence = correlation ** 2 if correlation != 0 else 0
        
        return TrendAnalysis(
            trend_type=trend_type,
            slope=slope,
            correlation=correlation,
            confidence=confidence,
            period_days=period_days,
            change_percentage=change_percentage
        )
    
    def check_alerts(self, series_type_name: str, family_member_id: Optional[int] = None) -> List[Dict]:
        """檢查警報"""
        alerts_triggered = []
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # 取得警報規則
            sql = """
            SELECT ta.*, tst.name as series_name, fm.name as family_member_name
            FROM time_series_alerts ta
            JOIN time_series_types tst ON ta.series_type_id = tst.id
            LEFT JOIN family_members fm ON ta.family_member_id = fm.id
            WHERE tst.name = %s AND ta.is_active = 1
            """
            params = [series_type_name]
            
            if family_member_id:
                sql += " AND (ta.family_member_id = %s OR ta.family_member_id IS NULL)"
                params.append(family_member_id)
            
            cursor.execute(sql, params)
            alert_rules = cursor.fetchall()
            
            for rule in alert_rules:
                # 取得最近的數據
                data_points = self.get_time_series_data(
                    series_type_name, 
                    family_member_id or rule['family_member_id'],
                    start_date=date.today() - timedelta(days=rule['period_days']),
                    end_date=date.today()
                )
                
                if not data_points:
                    continue
                
                current_value = data_points[-1].value
                alert_triggered = False
                message = ""
                
                if rule['condition_type'] == 'threshold_high' and rule['threshold_value']:
                    if current_value > float(rule['threshold_value']):
                        alert_triggered = True
                        message = f"{rule['series_name']} 超過上限警告：{current_value} > {rule['threshold_value']}"
                
                elif rule['condition_type'] == 'threshold_low' and rule['threshold_value']:
                    if current_value < float(rule['threshold_value']):
                        alert_triggered = True
                        message = f"{rule['series_name']} 低於下限警告：{current_value} < {rule['threshold_value']}"
                
                elif rule['condition_type'] == 'rapid_change' and rule['change_percentage']:
                    if len(data_points) >= 2:
                        old_value = data_points[0].value
                        change_pct = abs((current_value - old_value) / old_value * 100) if old_value != 0 else 0
                        if change_pct > float(rule['change_percentage']):
                            alert_triggered = True
                            message = f"{rule['series_name']} 快速變化警告：{rule['period_days']}天內變化{change_pct:.1f}%"
                
                elif rule['condition_type'] == 'trend_analysis':
                    trend = self.analyze_trend(data_points, rule['period_days'])
                    if trend.trend_type in ['increasing', 'decreasing'] and trend.confidence > 0.7:
                        alert_triggered = True
                        message = f"{rule['series_name']} 趨勢警告：{trend.trend_type} 趨勢，信心度{trend.confidence:.2f}"
                
                if alert_triggered:
                    alerts_triggered.append({
                        'alert_id': rule['id'],
                        'alert_name': rule['alert_name'],
                        'series_name': rule['series_name'],
                        'family_member': rule['family_member_name'],
                        'current_value': current_value,
                        'message': message,
                        'condition_type': rule['condition_type']
                    })
                    
                    # 記錄警報日誌
                    self._log_alert(rule['id'], current_value, 
                                  data_points[0].value if len(data_points) > 1 else current_value, 
                                  message)
            
            return alerts_triggered
            
        except Error as e:
            logger.error(f"檢查警報失敗: {e}")
            return []
    
    def _log_alert(self, alert_id: int, current_value: float, 
                  previous_value: float, message: str):
        """記錄警報日誌"""
        try:
            cursor = self.connection.cursor()
            sql = """
            INSERT INTO time_series_alert_logs 
            (alert_id, triggered_date, current_value, previous_value, message)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (alert_id, date.today(), current_value, previous_value, message))
            self.connection.commit()
        except Error as e:
            logger.error(f"記錄警報日誌失敗: {e}")
    
    def get_statistics_summary(self, series_type_name: str, 
                             family_member_id: Optional[int] = None,
                             period_days: int = 90) -> Dict[str, Any]:
        """取得統計摘要"""
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)
        
        data_points = self.get_time_series_data(
            series_type_name, family_member_id, start_date, end_date
        )
        
        if not data_points:
            return {}
        
        values = [point.value for point in data_points]
        trend = self.analyze_trend(data_points, period_days)
        
        summary = {
            'series_name': series_type_name,
            'period_days': period_days,
            'data_count': len(values),
            'latest_value': values[-1],
            'latest_date': data_points[-1].date.isoformat(),
            'min_value': min(values),
            'max_value': max(values),
            'average_value': statistics.mean(values),
            'median_value': statistics.median(values),
            'std_deviation': statistics.stdev(values) if len(values) > 1 else 0,
            'trend_analysis': {
                'trend_type': trend.trend_type,
                'change_percentage': trend.change_percentage,
                'confidence': trend.confidence
            }
        }
        
        return summary

def process_document_for_time_series(connection, document_id: int, ocr_text: str, 
                                   document_date: date, family_member_id: Optional[int] = None):
    """處理文件以提取時間序列數據"""
    analyzer = TimeSeriesAnalyzer(connection)
    extracted_data = analyzer.extract_numeric_values(ocr_text)
    
    success_count = 0
    for data in extracted_data:
        if analyzer.store_time_series_data(
            data['type'], data['value'], document_date, 
            family_member_id, document_id, data['confidence']
        ):
            success_count += 1
    
    logger.info(f"文件 {document_id} 成功提取並儲存 {success_count} 個時間序列數據點")
    return success_count
