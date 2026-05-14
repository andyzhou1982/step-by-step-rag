/**
 * Wiki Browser component for Day 8
 * Day 8 的 Wiki 浏览器组件
 *
 * Features:
 * - Browse and search Wiki pages
 * - View Wiki page content with linked pages
 * - Generate Wiki pages from uploaded documents
 * - Filter by concept tags
 */

import { useState, useEffect, useCallback } from 'react'
import {
  getWikiPages,
  getWikiPage,
  generateWikiPages,
  searchWikiPages,
  deleteWikiPage,
  getWikiStats,
  getWikiConcepts,
  WikiPageInfo,
  WikiPageDetail,
  WikiStats,
  WikiGenerateResponse
} from '../api/client'

type ViewMode = 'list' | 'detail' | 'generate'

function WikiBrowser() {
  // View state
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [pages, setPages] = useState<WikiPageInfo[]>([])
  const [totalPages, setTotalPages] = useState(0)
  const [selectedPage, setSelectedPage] = useState<WikiPageDetail | null>(null)
  const [stats, setStats] = useState<WikiStats | null>(null)
  const [concepts, setConcepts] = useState<string[]>([])

  // Search and filter
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedConcept, setSelectedConcept] = useState<string>('')
  const [searchResults, setSearchResults] = useState<any[]>([])

  // Generation state
  const [isGenerating, setIsGenerating] = useState(false)
  const [generateResult, setGenerateResult] = useState<WikiGenerateResponse | null>(null)

  // UI state
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load initial data
  useEffect(() => {
    loadPages()
    loadStats()
    loadConcepts()
  }, [])

  const loadPages = useCallback(async (concept?: string) => {
    setIsLoading(true)
    try {
      const response = await getWikiPages(100, 0, concept)
      setPages(response.pages)
      setTotalPages(response.total)
    } catch (e) {
      setError('Failed to load Wiki pages / 加载 Wiki 页面失败')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const loadStats = async () => {
    try {
      const s = await getWikiStats()
      setStats(s)
    } catch {}
  }

  const loadConcepts = async () => {
    try {
      const c = await getWikiConcepts()
      setConcepts(c)
    } catch {}
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([])
      return
    }
    setIsLoading(true)
    try {
      const results = await searchWikiPages(searchQuery, 10)
      setSearchResults(results)
    } catch {
      setError('Search failed / 搜索失败')
    } finally {
      setIsLoading(false)
    }
  }

  const handleGenerate = async () => {
    setIsGenerating(true)
    setGenerateResult(null)
    setError(null)
    try {
      const result = await generateWikiPages({ max_pages: 30 })
      setGenerateResult(result)
      // Refresh pages list
      await loadPages()
      await loadStats()
      await loadConcepts()
    } catch (e) {
      setError('Wiki generation failed / Wiki 生成失败')
    } finally {
      setIsGenerating(false)
    }
  }

  const handlePageClick = async (pageId: string) => {
    setIsLoading(true)
    try {
      const detail = await getWikiPage(pageId)
      setSelectedPage(detail)
      setViewMode('detail')
    } catch {
      setError('Failed to load page / 加载页面失败')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async (pageId: string) => {
    if (!confirm('Are you sure you want to delete this Wiki page?\n确定要删除此 Wiki 页面吗？')) return
    try {
      await deleteWikiPage(pageId)
      await loadPages(selectedConcept || undefined)
      await loadStats()
      if (selectedPage?.id === pageId) {
        setSelectedPage(null)
        setViewMode('list')
      }
    } catch {
      setError('Delete failed / 删除失败')
    }
  }

  const handleConceptFilter = (concept: string) => {
    const newConcept = concept === selectedConcept ? '' : concept
    setSelectedConcept(newConcept)
    loadPages(newConcept || undefined)
  }

  // ==================== Render: Detail View ====================
  if (viewMode === 'detail' && selectedPage) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <button
            onClick={() => { setViewMode('list'); setSelectedPage(null) }}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
          >
            &larr; Back to list / 返回列表
          </button>
          <button
            onClick={() => handleDelete(selectedPage.id)}
            className="px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 text-sm"
          >
            Delete / 删除
          </button>
        </div>

        {/* Page header */}
        <div className="bg-white rounded-lg shadow p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">{selectedPage.title}</h1>
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <span className="text-sm text-gray-500">v{selectedPage.version}</span>
            <span className="text-sm text-gray-500">|</span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
              selectedPage.confidence >= 0.7 ? 'bg-green-100 text-green-700' :
              selectedPage.confidence >= 0.4 ? 'bg-yellow-100 text-yellow-700' :
              'bg-red-100 text-red-700'
            }`}>
              {(selectedPage.confidence * 100).toFixed(0)}% confidence
            </span>
            {selectedPage.concepts.map((c, i) => (
              <span key={i} className="px-2 py-0.5 bg-blue-50 text-blue-600 rounded-full text-xs">
                {c}
              </span>
            ))}
          </div>
          {selectedPage.summary && (
            <p className="text-gray-600 text-sm mb-4">{selectedPage.summary}</p>
          )}
        </div>

        {/* Page content */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Content / 内容</h2>
          <div className="prose max-w-none text-gray-700 whitespace-pre-wrap">
            {selectedPage.content}
          </div>
        </div>

        {/* Linked pages */}
        {selectedPage.linked_pages.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">
              Related Pages ({selectedPage.linked_pages.length})
              / 相关页面
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {selectedPage.linked_pages.map((link, i) => (
                <button
                  key={i}
                  onClick={() => handlePageClick(link.page_id)}
                  className="text-left p-3 border rounded-lg hover:bg-gray-50"
                >
                  <p className="font-medium text-blue-600">{link.title}</p>
                  <p className="text-xs text-gray-500">
                    {link.relation_type} &middot; {link.direction}
                  </p>
                </button>
              ))}
            </div>
          </div>
        )}

        {error && <p className="text-red-500 text-sm">{error}</p>}
      </div>
    )
  }

  // ==================== Render: Generate View ====================
  if (viewMode === 'generate') {
    return (
      <div className="space-y-6">
        <button
          onClick={() => setViewMode('list')}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
        >
          &larr; Back to list / 返回列表
        </button>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">
            Generate Wiki Pages from Documents
            从文档生成 Wiki 页面
          </h2>
          <p className="text-gray-600 mb-4">
            This will use LLM to read all uploaded documents, extract key concepts,
            and generate structured Wiki pages with semantic search capability.
            <br />
            将使用 LLM 阅读所有上传的文档，提取核心概念，
            并生成支持语义搜索的结构化 Wiki 页面。
          </p>

          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className={`px-6 py-3 rounded-lg font-medium text-white ${
              isGenerating
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {isGenerating
              ? 'Generating... / 生成中...'
              : 'Generate Wiki Pages / 生成 Wiki 页面'
            }
          </button>

          {generateResult && (
            <div className="mt-6 p-4 bg-green-50 rounded-lg">
              <h3 className="font-medium text-green-800 mb-2">
                Generation Complete! / 生成完成！
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div>
                  <p className="text-green-600">Pages Created</p>
                  <p className="text-2xl font-bold text-green-800">{generateResult.pages_generated}</p>
                </div>
                <div>
                  <p className="text-green-600">Concepts Found</p>
                  <p className="text-2xl font-bold text-green-800">{generateResult.concepts_extracted}</p>
                </div>
                <div>
                  <p className="text-green-600">Links Created</p>
                  <p className="text-2xl font-bold text-green-800">{generateResult.links_created}</p>
                </div>
                <div>
                  <p className="text-green-600">Time (ms)</p>
                  <p className="text-2xl font-bold text-green-800">{generateResult.generation_time_ms.toFixed(0)}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {error && <p className="text-red-500 text-sm">{error}</p>}
      </div>
    )
  }

  // ==================== Render: List View ====================
  return (
    <div className="space-y-6">
      {/* Stats bar */}
      {stats && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg text-center">
            <p className="text-2xl font-bold text-blue-700">{stats.total_pages}</p>
            <p className="text-sm text-blue-600">Wiki Pages / Wiki 页面</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg text-center">
            <p className="text-2xl font-bold text-green-700">{stats.total_concepts}</p>
            <p className="text-sm text-green-600">Concepts / 概念</p>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg text-center">
            <p className="text-2xl font-bold text-purple-700">{stats.total_source_documents}</p>
            <p className="text-sm text-purple-600">Source Docs / 源文档</p>
          </div>
        </div>
      )}

      {/* Actions bar */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">
          Wiki Knowledge Base / Wiki 知识库
        </h2>
        <button
          onClick={() => setViewMode('generate')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
        >
          Generate Wiki / 生成 Wiki
        </button>
      </div>

      {/* Search */}
      <div className="flex gap-2">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Search Wiki pages semantically... / 语义搜索 Wiki 页面..."
          className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleSearch}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
        >
          Search / 搜索
        </button>
      </div>

      {/* Concept filter */}
      {concepts.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <span className="text-sm text-gray-500 self-center">Concepts:</span>
          {concepts.slice(0, 20).map((c) => (
            <button
              key={c}
              onClick={() => handleConceptFilter(c)}
              className={`px-2 py-1 rounded-full text-xs font-medium transition-colors ${
                selectedConcept === c
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      )}

      {/* Search results */}
      {searchResults.length > 0 && (
        <div>
          <h3 className="font-medium mb-3">
            Search Results / 搜索结果
          </h3>
          <div className="space-y-2">
            {searchResults.map((result, i) => (
              <button
                key={i}
                onClick={() => handlePageClick(result.page.id)}
                className="w-full text-left p-4 bg-white border rounded-lg hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-gray-900">{result.page.title}</p>
                    <p className="text-sm text-gray-500 mt-1">{result.page.summary}</p>
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      result.match_type === 'semantic' ? 'bg-green-50 text-green-600' : 'bg-yellow-50 text-yellow-600'
                    }`}>
                      {result.match_type}
                    </span>
                    <span className="text-sm text-gray-500">{(result.score * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Pages list */}
      {searchResults.length === 0 && (
        <div>
          <h3 className="font-medium mb-3">
            All Pages ({totalPages}) / 所有页面
          </h3>
          {isLoading ? (
            <p className="text-gray-500">Loading... / 加载中...</p>
          ) : pages.length === 0 ? (
            <div className="bg-gray-50 rounded-lg p-8 text-center">
              <p className="text-gray-500 mb-4">
                No Wiki pages yet. Generate pages from your uploaded documents.
                <br />
                尚无 Wiki 页面。从上传的文档生成页面。
              </p>
              <button
                onClick={() => setViewMode('generate')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
              >
                Generate Wiki / 生成 Wiki
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              {pages.map((page) => (
                <div
                  key={page.id}
                  className="flex items-center justify-between p-4 bg-white border rounded-lg hover:shadow-md transition-shadow"
                >
                  <button
                    onClick={() => handlePageClick(page.id)}
                    className="text-left flex-1"
                  >
                    <p className="font-medium text-gray-900">{page.title}</p>
                    {page.summary && (
                      <p className="text-sm text-gray-500 mt-1 line-clamp-2">{page.summary}</p>
                    )}
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs text-gray-400">v{page.version}</span>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        page.confidence >= 0.7 ? 'bg-green-100 text-green-700' :
                        page.confidence >= 0.4 ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {(page.confidence * 100).toFixed(0)}%
                      </span>
                      {page.concepts.slice(0, 3).map((c, i) => (
                        <span key={i} className="px-2 py-0.5 bg-blue-50 text-blue-600 rounded-full text-xs">
                          {c}
                        </span>
                      ))}
                      {page.concepts.length > 3 && (
                        <span className="text-xs text-gray-400">+{page.concepts.length - 3}</span>
                      )}
                    </div>
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDelete(page.id) }}
                    className="ml-4 text-gray-400 hover:text-red-500 text-sm"
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {error && <p className="text-red-500 text-sm">{error}</p>}
    </div>
  )
}

export default WikiBrowser
