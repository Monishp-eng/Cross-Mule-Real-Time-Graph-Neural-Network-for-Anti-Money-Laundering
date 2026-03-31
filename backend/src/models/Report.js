import mongoose from 'mongoose';

const reportSchema = new mongoose.Schema(
  {
    reportId: { type: String, required: true, unique: true, index: true },
    reportType: { type: String, required: true },
    status: { type: String, enum: ['generated', 'exported'], default: 'generated' },
    generatedAt: { type: Date, default: Date.now },
    meta: { type: Object, default: {} }
  },
  { timestamps: true }
);

export default mongoose.model('Report', reportSchema);
