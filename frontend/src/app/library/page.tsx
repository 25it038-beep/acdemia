'use client';

import { useState, useEffect, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { api } from '@/lib/api';
import { FileUpload } from '@/types';
import { motion } from 'framer-motion';
import { Upload, FileText, X, CheckCircle2, AlertCircle, Loader2, Search, Trash2 } from 'lucide-react';

const fileIcons: Record<string, string> = {
  pdf: '📄',
  docx: '📝',
  pptx: '📊',
  xlsx: '📈',
  csv: '📋',
  txt: '📃',
  md: '📑',
  zip: '📦',
  html: '🌐',
  py: '🐍',
  js: '📜',
  ts: '📘',
};

export default function LibraryPage() {
  const [files, setFiles] = useState<FileUpload[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [selectedSubject, setSelectedSubject] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [filesData, subjectsData] = await Promise.all([
        api.getFiles(),
        api.getSubjects(),
      ]);
      setFiles(filesData);
      setSubjects(subjectsData);
    } catch (err) {
      console.error('Failed to load library:', err);
    } finally {
      setLoading(false);
    }
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setUploading(true);
    try {
      for (const file of acceptedFiles) {
        await api.uploadFile(file, selectedSubject || undefined);
      }
      loadData();
    } catch (err) {
      console.error('Upload failed:', err);
    } finally {
      setUploading(false);
    }
  }, [selectedSubject]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
  });

  const deleteFile = async (id: string) => {
    await api.deleteFile(id);
    loadData();
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const statusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      case 'processing': return <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-red-400" />;
      default: return <AlertCircle className="w-4 h-4 text-yellow-400" />;
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText className="w-6 h-6 text-indigo-400" />
          <div>
            <h1 className="text-xl font-bold text-white">Library</h1>
            <p className="text-sm text-white/40">{files.length} files</p>
          </div>
        </div>
        <select
          value={selectedSubject}
          onChange={(e) => setSelectedSubject(e.target.value)}
          className="input-glass w-48 text-sm"
        >
          <option value="">All subjects</option>
          {subjects.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
      </div>

      {/* Upload Zone */}
      <div
        {...getRootProps()}
        className={`glass rounded-2xl border-2 border-dashed p-12 text-center cursor-pointer transition-all ${
          isDragActive
            ? 'border-indigo-500 bg-indigo-500/5'
            : 'border-white/10 hover:border-white/20'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 text-white/20 mx-auto mb-4" />
        <p className="text-white/60 mb-1">
          {isDragActive ? 'Drop files here...' : 'Drag & drop files here'}
        </p>
        <p className="text-white/40 text-sm">
          PDF, DOCX, PPTX, XLSX, CSV, TXT, MD, EPUB, ZIP, HTML, Images, Videos, Audio
        </p>
        {uploading && (
          <div className="flex items-center justify-center gap-2 mt-4 text-indigo-400 text-sm">
            <Loader2 className="w-4 h-4 animate-spin" />
            Uploading...
          </div>
        )}
      </div>

      {/* File List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {files.map((file) => (
            <motion.div
              key={file.id}
              layout
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="card group relative"
            >
              <button
                onClick={() => deleteFile(file.id)}
                className="absolute top-3 right-3 w-7 h-7 rounded-lg bg-white/5 hover:bg-red-500/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all"
              >
                <Trash2 className="w-3.5 h-3.5 text-red-400" />
              </button>

              <div className="flex items-center gap-3 mb-3">
                <span className="text-2xl">{fileIcons[file.file_type] || '📄'}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{file.original_filename}</p>
                  <p className="text-xs text-white/40">{file.file_type.toUpperCase()} - {formatSize(file.file_size)}</p>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs text-white/40">
                <div className="flex items-center gap-1">
                  {statusIcon(file.status)}
                  <span className="capitalize">{file.status}</span>
                </div>
                {file.pages > 0 && <span>{file.pages} pages</span>}
                {file.chunks > 0 && <span>{file.chunks} chunks</span>}
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}