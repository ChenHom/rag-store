'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface SearchFilters {
  categories: Array<{name: string; icon: string; color: string}>;
  tags: Array<{name: string; color: string}>;
  family_members: string[];
  amount_ranges: Array<{label: string; min: number; max: number}>;
  date_ranges: Array<{month: string; count: number}>;
}

interface SearchResult {
  doc_id: string;
  chunk: string;
  distance: number;
  filename: string;
  category: string;
  document_date: string;
  extracted_amount: number | null;
  family_member: string;
}

interface AdvancedSearchResponse {
  results: SearchResult[];
  statistics: {
    total_results: number;
    categories_found: number;
    date_range: {earliest: string; latest: string};
    amount_range: {min: number; max: number};
  };
  search_parameters: {
    query: string;
    category?: string;
    tags?: string[];
    family_member?: string;
    date_from?: string;
    date_to?: string;
    amount_min?: number;
    amount_max?: number;
    search_mode: string;
  };
}

export default function AdvancedSearchPage() {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<SearchFilters | null>(null);
  const [selectedFilters, setSelectedFilters] = useState({
    category: '',
    tags: [] as string[],
    family_member: '',
    date_from: '',
    date_to: '',
    amount_min: '',
    amount_max: '',
    search_mode: 'hybrid'
  });
  const [searchResults, setSearchResults] = useState<AdvancedSearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingFilters, setIsLoadingFilters] = useState(true);

  const router = useRouter();

  // 載入搜尋過濾器選項
  useEffect(() => {
    const loadFilters = async () => {
      try {
        const response = await fetch('/api/search/filters');
        if (response.ok) {
          const data = await response.json();
          setFilters(data);
        }
      } catch (error) {
        console.error('Failed to load filters:', error);
      } finally {
        setIsLoadingFilters(false);
      }
    };

    loadFilters();
  }, []);

  // 執行進階搜尋
  const handleAdvancedSearch = async () => {
    if (!query.trim()) {
      alert('請輸入搜尋關鍵字');
      return;
    }

    setIsLoading(true);
    try {
      const searchParams = {
        query: query.trim(),
        category: selectedFilters.category || undefined,
        tags: selectedFilters.tags.length > 0 ? selectedFilters.tags : undefined,
        family_member: selectedFilters.family_member || undefined,
        date_from: selectedFilters.date_from || undefined,
        date_to: selectedFilters.date_to || undefined,
        amount_min: selectedFilters.amount_min ? parseFloat(selectedFilters.amount_min) : undefined,
        amount_max: selectedFilters.amount_max ? parseFloat(selectedFilters.amount_max) : undefined,
        search_mode: selectedFilters.search_mode
      };

      const response = await fetch('/api/search/advanced', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(searchParams)
      });

      if (response.ok) {
        const data = await response.json();
        setSearchResults(data);
      } else {
        const error = await response.text();
        alert(`搜尋失敗: ${error}`);
      }
    } catch (error) {
      console.error('Search failed:', error);
      alert('搜尋時發生錯誤');
    } finally {
      setIsLoading(false);
    }
  };

  // 處理標籤選擇
  const handleTagToggle = (tagName: string) => {
    setSelectedFilters(prev => ({
      ...prev,
      tags: prev.tags.includes(tagName)
        ? prev.tags.filter(t => t !== tagName)
        : [...prev.tags, tagName]
    }));
  };

  // 清除所有過濾器
  const clearFilters = () => {
    setSelectedFilters({
      category: '',
      tags: [],
      family_member: '',
      date_from: '',
      date_to: '',
      amount_min: '',
      amount_max: '',
      search_mode: 'hybrid'
    });
  };

  if (isLoadingFilters) {
    return (
      <div className="container mx-auto p-4">
        <div className="text-center">載入中...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 max-w-6xl">
      {/* 頁面標題 */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">🔍 進階搜尋</h1>
        <p className="text-gray-600">使用多維度條件精確搜尋您的文件</p>
      </div>

      {/* 搜尋區域 */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        {/* 基本搜尋 */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">搜尋關鍵字</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="輸入您要搜尋的內容..."
              className="flex-1 p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              onKeyPress={(e) => e.key === 'Enter' && handleAdvancedSearch()}
            />
            <button
              onClick={handleAdvancedSearch}
              disabled={isLoading}
              className="px-6 py-3 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50"
            >
              {isLoading ? '搜尋中...' : '搜尋'}
            </button>
          </div>
        </div>

        {/* 搜尋模式 */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">搜尋模式</label>
          <div className="flex gap-4">
            {[
              { value: 'semantic', label: '語義搜尋', desc: '基於內容理解' },
              { value: 'filter', label: '條件過濾', desc: '基於元資料篩選' },
              { value: 'hybrid', label: '混合模式', desc: '結合語義和過濾' }
            ].map(mode => (
              <label key={mode.value} className="flex items-center">
                <input
                  type="radio"
                  name="search_mode"
                  value={mode.value}
                  checked={selectedFilters.search_mode === mode.value}
                  onChange={(e) => setSelectedFilters(prev => ({ ...prev, search_mode: e.target.value }))}
                  className="mr-2"
                />
                <div>
                  <div className="font-medium">{mode.label}</div>
                  <div className="text-xs text-gray-500">{mode.desc}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* 過濾器 */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* 分類過濾 */}
          <div>
            <label className="block text-sm font-medium mb-2">文件分類</label>
            <select
              value={selectedFilters.category}
              onChange={(e) => setSelectedFilters(prev => ({ ...prev, category: e.target.value }))}
              className="w-full p-2 border border-gray-300 rounded-md"
            >
              <option value="">所有分類</option>
              {filters?.categories.map(cat => (
                <option key={cat.name} value={cat.name}>
                  {cat.icon} {cat.name}
                </option>
              ))}
            </select>
          </div>

          {/* 家庭成員過濾 */}
          <div>
            <label className="block text-sm font-medium mb-2">家庭成員</label>
            <select
              value={selectedFilters.family_member}
              onChange={(e) => setSelectedFilters(prev => ({ ...prev, family_member: e.target.value }))}
              className="w-full p-2 border border-gray-300 rounded-md"
            >
              <option value="">所有成員</option>
              {filters?.family_members.map(member => (
                <option key={member} value={member}>{member}</option>
              ))}
            </select>
          </div>

          {/* 日期範圍 */}
          <div>
            <label className="block text-sm font-medium mb-2">日期範圍</label>
            <div className="flex gap-2">
              <input
                type="date"
                value={selectedFilters.date_from}
                onChange={(e) => setSelectedFilters(prev => ({ ...prev, date_from: e.target.value }))}
                className="flex-1 p-2 border border-gray-300 rounded-md text-sm"
              />
              <input
                type="date"
                value={selectedFilters.date_to}
                onChange={(e) => setSelectedFilters(prev => ({ ...prev, date_to: e.target.value }))}
                className="flex-1 p-2 border border-gray-300 rounded-md text-sm"
              />
            </div>
          </div>

          {/* 金額範圍 */}
          <div>
            <label className="block text-sm font-medium mb-2">金額範圍</label>
            <div className="flex gap-2">
              <input
                type="number"
                placeholder="最小金額"
                value={selectedFilters.amount_min}
                onChange={(e) => setSelectedFilters(prev => ({ ...prev, amount_min: e.target.value }))}
                className="flex-1 p-2 border border-gray-300 rounded-md text-sm"
              />
              <input
                type="number"
                placeholder="最大金額"
                value={selectedFilters.amount_max}
                onChange={(e) => setSelectedFilters(prev => ({ ...prev, amount_max: e.target.value }))}
                className="flex-1 p-2 border border-gray-300 rounded-md text-sm"
              />
            </div>
          </div>
        </div>

        {/* 標籤選擇 */}
        {filters?.tags && filters.tags.length > 0 && (
          <div className="mt-4">
            <label className="block text-sm font-medium mb-2">標籤篩選</label>
            <div className="flex flex-wrap gap-2">
              {filters.tags.map(tag => (
                <button
                  key={tag.name}
                  onClick={() => handleTagToggle(tag.name)}
                  className={`px-3 py-1 rounded-full text-sm border ${
                    selectedFilters.tags.includes(tag.name)
                      ? 'bg-blue-500 text-white border-blue-500'
                      : 'bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200'
                  }`}
                  style={selectedFilters.tags.includes(tag.name) ? {} : { color: tag.color }}
                >
                  {tag.name}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* 操作按鈕 */}
        <div className="mt-4 flex gap-2">
          <button
            onClick={clearFilters}
            className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
          >
            清除過濾器
          </button>
          <button
            onClick={() => router.push('/chat')}
            className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600"
          >
            返回聊天搜尋
          </button>
        </div>
      </div>

      {/* 搜尋結果 */}
      {searchResults && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold mb-4">搜尋結果</h2>
          
          {/* 統計資訊 */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-blue-600">{searchResults.statistics.total_results}</div>
                <div className="text-sm text-gray-600">總結果數</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">{searchResults.statistics.categories_found}</div>
                <div className="text-sm text-gray-600">分類數量</div>
              </div>
              <div>
                <div className="text-lg font-bold text-purple-600">
                  ${searchResults.statistics.amount_range.min || 0} - ${searchResults.statistics.amount_range.max || 0}
                </div>
                <div className="text-sm text-gray-600">金額範圍</div>
              </div>
              <div>
                <div className="text-sm font-bold text-orange-600">
                  {searchResults.statistics.date_range.earliest} ~ {searchResults.statistics.date_range.latest}
                </div>
                <div className="text-sm text-gray-600">日期範圍</div>
              </div>
            </div>
          </div>

          {/* 結果列表 */}
          <div className="space-y-4">
            {searchResults.results.map((result, index) => (
              <div key={`${result.doc_id}-${index}`} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg">{result.filename}</h3>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {result.category && (
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                          {result.category}
                        </span>
                      )}
                      {result.family_member && (
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                          {result.family_member}
                        </span>
                      )}
                      {result.document_date && (
                        <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded-full">
                          {result.document_date}
                        </span>
                      )}
                      {result.extracted_amount && (
                        <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                          ${result.extracted_amount}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="text-xs text-gray-500">
                    相似度: {(1 - result.distance).toFixed(3)}
                  </div>
                </div>
                
                <div className="text-gray-700 text-sm">
                  {result.chunk.substring(0, 300)}
                  {result.chunk.length > 300 && '...'}
                </div>
              </div>
            ))}
          </div>

          {searchResults.results.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              沒有找到符合條件的結果
            </div>
          )}
        </div>
      )}
    </div>
  );
}
