const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, Header, Footer, AlignmentType, HeadingLevel, BorderStyle,
  WidthType, ShadingType, VerticalAlign, PageNumber, PageBreak,
  LevelFormat, TabStopType, TabStopPosition
} = require('docx');
const fs = require('fs');
const path = require('path');

const BASE = '/Users/aphchat/Coding Year 1/KIVY_Project/Panguin-pikachu';

// ─── helpers ────────────────────────────────────────────────────────────────
const FONT = 'TH Sarabun New';
const SZ   = 32;   // 16pt = 32 half-points
const SZ_S = 28;   // 14pt for captions
const SZ_H1 = 40; // 20pt
const SZ_H2 = 36; // 18pt
const SZ_H3 = 32; // 16pt bold

// A4 with 1-inch margins → content = 11906 - 2880 = 9026 DXA
const CONTENT_W = 9026;

const BORDER = { style: BorderStyle.SINGLE, size: 1, color: 'BBBBBB' };
const CELL_BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 60, after: 120 },
    alignment: opts.center ? AlignmentType.CENTER : AlignmentType.JUSTIFIED,
    children: [new TextRun({
      text,
      font: FONT,
      size: opts.size || SZ,
      bold: opts.bold || false,
      italics: opts.italic || false,
      color: opts.color || '000000',
    })],
    ...opts.extra,
  });
}

function h(level, text) {
  const sizes = { 1: SZ_H1, 2: SZ_H2, 3: SZ_H3 };
  const headingLevels = {
    1: HeadingLevel.HEADING_1,
    2: HeadingLevel.HEADING_2,
    3: HeadingLevel.HEADING_3,
  };
  return new Paragraph({
    heading: headingLevels[level],
    spacing: { before: 240, after: 120 },
    children: [new TextRun({ text, font: FONT, size: sizes[level], bold: true })],
  });
}

function caption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 60, after: 200 },
    children: [new TextRun({ text, font: FONT, size: SZ_S, italics: true, color: '444444' })],
  });
}

function blank() {
  return new Paragraph({ spacing: { before: 0, after: 0 }, children: [new TextRun('')] });
}

function img(relPath, w, h, altText) {
  const fullPath = path.join(BASE, relPath);
  const data = fs.readFileSync(fullPath);
  const ext = path.extname(relPath).slice(1).toLowerCase();
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 100, after: 60 },
    children: [new ImageRun({
      type: ext === 'jpg' ? 'jpeg' : ext,
      data,
      transformation: { width: w, height: h },
      altText: { title: altText, description: altText, name: altText },
    })],
  });
}

// ─── table builder ──────────────────────────────────────────────────────────
function makeTable(headers, rows, colWidths) {
  const totalW = colWidths.reduce((a, b) => a + b, 0);
  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map((h, i) =>
      new TableCell({
        borders: CELL_BORDERS,
        width: { size: colWidths[i], type: WidthType.DXA },
        shading: { fill: '1F4E79', type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        verticalAlign: VerticalAlign.CENTER,
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: h, font: FONT, size: SZ_S, bold: true, color: 'FFFFFF' })],
        })],
      })
    ),
  });

  const dataRows = rows.map((row, ri) =>
    new TableRow({
      children: row.map((cell, ci) =>
        new TableCell({
          borders: CELL_BORDERS,
          width: { size: colWidths[ci], type: WidthType.DXA },
          shading: { fill: ri % 2 === 0 ? 'EBF3FB' : 'FFFFFF', type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: String(cell), font: FONT, size: SZ_S })],
          })],
        })
      ),
    })
  );

  return new Table({
    width: { size: totalW, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [headerRow, ...dataRows],
  });
}

// ─── bullet helper ──────────────────────────────────────────────────────────
function bullet(text) {
  return new Paragraph({
    numbering: { reference: 'bullets', level: 0 },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, font: FONT, size: SZ })],
  });
}

// ╔══════════════════════════════════════════════════════════╗
// ║                   BUILD DOCUMENT                        ║
// ╚══════════════════════════════════════════════════════════╝

const doc = new Document({
  numbering: {
    config: [{
      reference: 'bullets',
      levels: [{ level: 0, format: LevelFormat.BULLET, text: '•',
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }],
    }],
  },
  styles: {
    default: {
      document: { run: { font: FONT, size: SZ } },
    },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: FONT, size: SZ_H1, bold: true, color: '1F4E79' },
        paragraph: { spacing: { before: 360, after: 120 }, outlineLevel: 0,
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: '1F4E79', space: 1 } } } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: FONT, size: SZ_H2, bold: true, color: '2E75B6' },
        paragraph: { spacing: { before: 240, after: 80 }, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: FONT, size: SZ_H3, bold: true, color: '2F5496' },
        paragraph: { spacing: { before: 200, after: 60 }, outlineLevel: 2 } },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 }, // A4
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          border: { bottom: { style: BorderStyle.SINGLE, size: 2, color: '1F4E79', space: 1 } },
          children: [new TextRun({
            text: 'The Great Melt — เพนกวิน แดช  |  NSC 2026',
            font: FONT, size: 24, color: '555555',
          })],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          border: { top: { style: BorderStyle.SINGLE, size: 2, color: '1F4E79', space: 1 } },
          children: [
            new TextRun({ text: 'หน้า ', font: FONT, size: 24, color: '555555' }),
            new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 24, color: '555555' }),
          ],
        })],
      }),
    },

    children: [

      // ══════════════════════════════════════
      // หน้าปก
      // ══════════════════════════════════════
      blank(), blank(), blank(),
      p('รหัสโครงการ  ...................................', { center: true, size: SZ_S }),
      blank(),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 60, after: 60 },
        children: [new TextRun({ text: 'The Great Melt — เพนกวิน แดช', font: FONT, size: 52, bold: true, color: '1F4E79' })],
      }),
      p('หมวด 12: โปรแกรมเพื่อส่งเสริมทักษะการเรียนรู้', { center: true, size: SZ }),
      p('ระดับนิสิต นักศึกษา', { center: true }),
      blank(), blank(),
      p('รายงานฉบับสมบูรณ์', { center: true, bold: true, size: SZ_H2 }),
      p('เสนอต่อ', { center: true }),
      p('สำนักงานพัฒนาวิทยาศาสตร์และเทคโนโลยีแห่งชาติ', { center: true, bold: true }),
      p('กระทรวงการอุดมศึกษา วิทยาศาสตร์ วิจัยและนวัตกรรม', { center: true }),
      blank(),
      p('ได้รับทุนอุดหนุนโครงการวิจัย พัฒนาและวิศวกรรม', { center: true }),
      p('โครงการแข่งขันพัฒนาโปรแกรมคอมพิวเตอร์แห่งประเทศไทย ครั้งที่ 28', { center: true, bold: true }),
      p('ประจำปีงบประมาณ 2569', { center: true }),
      blank(), blank(),
      p('โดย', { center: true }),
      p('ชื่อผู้พัฒนา  นายอภิชาติ จะหย่อ', { center: true }),
      p('ชื่อผู้พัฒนา  ..............................................................................................', { center: true }),
      p('ชื่อผู้พัฒนา  .............................................................................................', { center: true }),
      p('ชื่ออาจารย์ที่ปรึกษาโครงการ  ดร. ธนาธิป ลิ่มนา', { center: true }),
      p('ชื่อสถาบันการศึกษา  มหาวิทยาลัยสงขลานครินทร์', { center: true }),
      p('จังหวัด  สงขลา', { center: true }),

      new Paragraph({ children: [new PageBreak()] }),

      // ══════════════════════════════════════
      // 2. Executive Summary
      // ══════════════════════════════════════
      h(1, '2. สาระสำคัญของโครงการและคำสำคัญ (Executive Summary & Keywords)'),
      h(2, '2.1 สาระสำคัญของโครงการ'),
      p('การเปลี่ยนแปลงสภาพภูมิอากาศเป็นวิกฤตการณ์ที่มีหลักฐานเชิงประจักษ์รองรับอย่างชัดเจน รายงาน AR6 ของคณะกรรมการระหว่างรัฐบาลว่าด้วยการเปลี่ยนแปลงสภาพภูมิอากาศ (IPCC, 2023) ระบุว่าการสะสมของก๊าซเรือนกระจกในชั้นบรรยากาศนับตั้งแต่ยุคอุตสาหกรรมเป็นสาเหตุหลักของการเพิ่มขึ้นของอุณหภูมิโลก ส่งผลให้เกิดลำดับของวิกฤตสิ่งแวดล้อมที่เชื่อมโยงกัน ได้แก่ การละลายของน้ำแข็งขั้วโลก การยกตัวของระดับน้ำทะเล ความถี่ของภัยแล้ง น้ำท่วม และไฟป่าที่เพิ่มขึ้นอย่างมีนัยสำคัญ เพนกวินสายพันธุ์ Emperor ซึ่งพึ่งพาน้ำแข็งทะเลในวัฏจักรการเพาะพันธุ์มีความเสี่ยงสูญพันธุ์ถึงร้อยละ 98 ภายในปี ค.ศ. 2100 ภายใต้สถานการณ์การปล่อยก๊าซเรือนกระจกสูง (Jenouvrier et al., 2019)'),
      p('โครงการ "The Great Melt — เพนกวิน แดช" พัฒนาขึ้นเพื่อตอบสนองต่อปรากฏการณ์ Psychological Distance ซึ่ง Trope และ Liberman (2010) อธิบายว่าเป็นสาเหตุที่ทำให้มนุษย์ไม่แปลงข้อมูลวิทยาศาสตร์เกี่ยวกับสิ่งแวดล้อมให้กลายเป็นแรงกระตุ้นในการปรับเปลี่ยนพฤติกรรม เกมใช้กลไก Agency, Emotional Anchoring และ Immediate Feedback Loop ของวิดีโอเกม (Mayer, 2019) เพื่อลดระยะห่างทางจิตวิทยาดังกล่าว ผ่านการให้ผู้เล่นสัมผัสผลพวงของภาวะโลกร้อนโดยตรงในทุกการตัดสินใจภายในเกม'),
      p('ในด้านวิศวกรรมซอฟต์แวร์ แอปพลิเคชันพัฒนาด้วยภาษา Python 3.12 บน Kivy Framework เวอร์ชัน 2.3.1 ซึ่งใช้การเร่งความเร็วกราฟิกผ่าน OpenGL ES 2.0 สามารถรักษาอัตราเฟรมที่ 60 FPS หรือมากกว่าได้บนฮาร์ดแวร์สเปกพื้นฐาน ระบบออกแบบตามหลัก Green Software Engineering โดยประยุกต์ใช้ Object Pooling Pattern, Procedural Content Generation และ Singleton Pattern เพื่อลดการใช้ทรัพยากรประมวลผล'),
      h(2, '2.2 คำสำคัญ (Keywords)'),
      p('Climate Change Awareness · Psychological Distance Reduction · Gamification · Green Software Engineering · Procedural Content Generation (PCG) · Isometric Projection · Object Pooling · Dynamic Difficulty Scaling · Python · Kivy · SDG 13 — Climate Action', { italic: true }),

      new Paragraph({ children: [new PageBreak()] }),

      // ══════════════════════════════════════
      // 3. หลักการและเหตุผล
      // ══════════════════════════════════════
      h(1, '3. หลักการและเหตุผล (Rationale)'),
      h(2, '3.1 วิกฤตการณ์สิ่งแวดล้อม: จากมาตราส่วนดาวเคราะห์สู่มาตราส่วนมนุษย์'),
      p('นับตั้งแต่การปฏิวัติอุตสาหกรรมเมื่อราว 200 ปีที่แล้ว มนุษยชาติได้ปล่อยคาร์บอนไดออกไซด์และก๊าซเรือนกระจกชนิดอื่นสะสมในชั้นบรรยากาศในปริมาณที่ไม่เคยปรากฏในประวัติศาสตร์ 800,000 ปี (Lüthi et al., 2008) รายงาน AR6 ของ IPCC (2023) คาดการณ์ว่าหากไม่มีมาตรการลดการปล่อยก๊าซเรือนกระจกอย่างเร่งด่วน อุณหภูมิเฉลี่ยโลกจะเพิ่มขึ้นถึง 2.7 องศาเซลเซียสภายในปี ค.ศ. 2100 ส่งผลให้ระดับน้ำทะเลสูงขึ้นในช่วง 0.28–1.01 เมตร และกระทบประชากรชายฝั่งกว่าหนึ่งพันล้านคน'),
      p('การหดตัวของแผ่นน้ำแข็งอาร์กติกในอัตราร้อยละ 13 ต่อทศวรรษนับตั้งแต่ปี ค.ศ. 1979 (NSIDC, 2023) เร่งให้เกิด Ice-Albedo Feedback Loop กล่าวคือ เมื่อพื้นผิวน้ำแข็งสีขาวลดลง มหาสมุทรซึ่งมีค่า Albedo ต่ำกว่าจะดูดซับความร้อนมากขึ้น ส่งผลให้อุณหภูมิสูงขึ้นและน้ำแข็งละลายเร็วขึ้นในลักษณะป้อนกลับแบบทบทวี ภัยแล้งที่รุนแรงขึ้นส่งผลให้ประชากรกว่าหนึ่งพันล้านคนทั่วโลกเผชิญกับความเครียดด้านน้ำ และเหตุการณ์น้ำท่วมรุนแรงมีความถี่เพิ่มขึ้นสามเท่านับตั้งแต่ปี ค.ศ. 1980 (WMO, 2023)'),
      h(2, '3.2 ช่องว่างระหว่างการรับรู้และการเปลี่ยนแปลงพฤติกรรม'),
      p('งานวิจัยของ Yale Program on Climate Change Communication (2022) พบว่าแม้ร้อยละ 70 ของเยาวชนทั่วโลกจะยอมรับว่าภาวะโลกร้อนเป็นปัญหาจริง แต่น้อยกว่าร้อยละ 30 ระบุว่าตนรู้สึกว่าเป็นเรื่องที่เกี่ยวข้องกับชีวิตประจำวัน ช่องว่างนี้อธิบายได้ด้วย Construal Level Theory ของ Trope และ Liberman (2010) ซึ่งระบุว่ามนุษย์ประมวลผลข้อมูลในระดับนามธรรมสูงเมื่อเหตุการณ์รู้สึกไกลในมิติใดมิติหนึ่งจากสี่ประการ ได้แก่ เวลา พื้นที่ ความไม่แน่นอน และความไม่เกี่ยวข้องส่วนตัว'),
      h(2, '3.3 วิดีโอเกมในฐานะสื่อลด Psychological Distance'),
      p('Mayer (2019) รวบรวมหลักฐานจากงานวิจัย Game-based Learning และระบุคุณสมบัติพิเศษสามประการของวิดีโอเกม: (1) Agency — ผู้เล่นเป็นผู้กระทำ ไม่ใช่ผู้สังเกต, (2) Emotional Anchoring — เกมสร้างความผูกพันทางอารมณ์ผ่านกลไกและสัญญาณโสตทัศน์, (3) Immediate Feedback Loop — เกมให้ผลลัพธ์ทันที ซึ่งตรงข้ามกับวิกฤตสิ่งแวดล้อมที่ผลกระทบมักปรากฏหลายสิบปีต่อมา'),
      h(2, '3.4 ระบบ Active Learning Quiz: การเรียนรู้ที่ฝังในกลไกเกม'),
      p('Freeman et al. (2014) วิเคราะห์การศึกษา 225 ชิ้น และพบว่า Active Learning เพิ่มผลการเรียนรู้เฉลี่ย 0.47 Standard Deviation เมื่อเทียบกับ Passive Learning Roediger และ Butler (2011) พิสูจน์ว่าการถูกทดสอบซ้ำ (Testing Effect) เพิ่มการจดจำระยะยาวได้ดีกว่าการอ่านซ้ำถึงร้อยละ 50'),
      h(2, '3.5 หลักการ Green Software Engineering'),
      p('Pihkola et al. (2018) ประเมินว่าการลดการใช้ CPU ของซอฟต์แวร์ลงร้อยละ 10 สามารถลด Carbon Footprint ของการประมวลผลในระดับที่วัดได้จริง โครงการนี้จึงออกแบบให้ทำงานบนฮาร์ดแวร์สเปกพื้นฐาน เพื่อยืดอายุอุปกรณ์และลด Electronic Waste ตามแนวทาง Green Computing (Murugesan, 2008)'),

      new Paragraph({ children: [new PageBreak()] }),

      // ══════════════════════════════════════
      // 4. วัตถุประสงค์
      // ══════════════════════════════════════
      h(1, '4. วัตถุประสงค์ (Objectives)'),
      p('4.1  เพื่อพัฒนาซอฟต์แวร์เกมประเภท Endless Runner บนมุมมอง Isometric'),
      p('4.2  เพื่อออกแบบและนำ Dynamic Difficulty Scaling Algorithm ที่ปรับระดับความยากตามระยะทางแบบ Continuous Function มาใช้ เพื่อรักษา Flow State ของผู้เล่น'),
      p('4.3  เพื่อพิสูจน์หลักการ Green Software Engineering ผ่านการนำ Object Pooling Pattern, Lazy Texture Loading และ Grid-based O(1) Collision Detection มาใช้ ให้ซอฟต์แวร์รักษา Frame Rate ≥ 60 FPS บนฮาร์ดแวร์ที่มี RAM ≥ 4 GB'),

      // ══════════════════════════════════════
      // 5. ปัญหา
      // ══════════════════════════════════════
      h(1, '5. ปัญหาหรือประโยชน์ที่เป็นเหตุผลให้ควรพัฒนาโปรแกรม'),
      h(2, '5.1 การวิเคราะห์สภาพปัญหา (Problem Analysis)'),
      p('ปัญหาที่ 1 — Psychological Distance ในการสื่อสารสิ่งแวดล้อม', { bold: true }),
      p('ข้อมูลจาก Yale Program on Climate Change Communication (2022) ชี้ว่าแม้ร้อยละ 70 ของเยาวชนทั่วโลกจะยอมรับว่าภาวะโลกร้อนเป็นปัญหาจริง แต่น้อยกว่าร้อยละ 30 ระบุว่าตนรู้สึกว่าเป็นเรื่องที่เกี่ยวข้องกับชีวิตประจำวัน ช่องว่างนี้อธิบายได้ด้วย Construal Level Theory ตามที่ Trope และ Liberman (2010) อธิบาย'),

      // === ADDITION 1: Thai context paragraph added after Trope & Liberman reference ===
      p('สำหรับบริบทประเทศไทยโดยเฉพาะ ประเทศไทยอยู่อันดับที่ 9 จาก 181 ประเทศในด้านความเสี่ยงต่อภัยพิบัติจากสภาพอากาศ (Germanwatch, 2021) แต่คะแนน PISA 2022 ด้านวิทยาศาสตร์ของนักเรียนไทยอยู่ที่ 421 คะแนน ต่ำกว่าค่าเฉลี่ย OECD ที่ 485 คะแนน (OECD, 2023) สะท้อนให้เห็นว่ากลุ่มประชากรที่มีความเสี่ยงสูงสุดจากวิกฤตสิ่งแวดล้อมกลับมีพื้นฐานความรู้ทางวิทยาศาสตร์ต่ำกว่าค่าเฉลี่ยโลก นักเรียนในระบบการศึกษาไทยระดับมัธยมศึกษามีจำนวนกว่า 3.4 ล้านคน (กระทรวงศึกษาธิการ, 2566) ซึ่งเป็นกลุ่มเป้าหมายที่มีนัยสำคัญหากมีสื่อการเรียนรู้ที่เข้าถึงได้และน่าสนใจ'),

      p('ปัญหาที่ 2 — Resource Intensity ของ Edutainment Software', { bold: true }),
      p('สื่อปฏิสัมพันธ์เชิงการศึกษาส่วนใหญ่ต้องการฮาร์ดแวร์ระดับกลางถึงสูง ทำให้ไม่สามารถนำไปใช้ในสถาบันการศึกษาที่มีทรัพยากรจำกัด ขัดกับเป้าหมาย SDG 4 และ SDG 10'),
      p('ปัญหาที่ 3 — ขาดสื่อ Edutainment ภาษาไทยด้านสิ่งแวดล้อม', { bold: true }),
      p('ประเทศไทยอยู่อันดับที่ 9 จาก 181 ประเทศตาม Global Climate Risk Index (Germanwatch, 2021) แต่มีสื่อ Edutainment ภาษาไทยเกี่ยวกับเรื่องนี้น้อยมาก'),
      p('ปัญหาที่ 4 — การเรียนรู้แบบ Passive ในสื่อสิ่งแวดล้อม', { bold: true }),
      p('Freeman et al. (2014) พิสูจน์ว่า Active Learning เพิ่มผลการเรียนรู้ 0.47 SD เมื่อเทียบ Passive Learning ในทุกสาขาวิชา'),
      h(2, '5.2 ประโยชน์และคุณค่าของโครงการ (Value Proposition)'),
      p('มิติเชิงสังคมและการศึกษา:', { bold: true }),
      p('ระบบ Biome Progression ที่เปลี่ยนสภาพแวดล้อมตามระยะทางทำให้ผู้เล่นสัมผัสลำดับวิกฤตสิ่งแวดล้อมผ่าน Active Learning ตามหลักการ Situated Cognition (Brown, Collins & Duguid, 1989)'),
      p('มิติเชิงสิ่งแวดล้อม:', { bold: true }),
      p('สถาปัตยกรรม Green IT ที่ใช้ Object Pooling ลดการทำงานของ Garbage Collector ยืดอายุฮาร์ดแวร์รุ่นเก่า และลด Electronic Waste โดยตรง'),
      p('มิติเชิงเศรษฐกิจ:', { bold: true }),
      p('ซอฟต์แวร์เป็น Standalone Application ที่ไม่ต้องการการเชื่อมต่ออินเทอร์เน็ต รองรับคอมพิวเตอร์สเปกพื้นฐานในสถาบันการศึกษา'),

      new Paragraph({ children: [new PageBreak()] }),

      // ══════════════════════════════════════
      // 6. เป้าหมายและขอบเขต
      // ══════════════════════════════════════
      h(1, '6. เป้าหมายและขอบเขตของโครงการ (Project Goals & Scope)'),
      h(2, '6.1 เป้าหมายที่วัดผลได้ (Measurable Key Results)'),
      blank(),
      makeTable(
        ['ด้าน', 'เป้าหมาย', 'วิธีวัด'],
        [
          ['Frame Rate', '≥ 60 FPS ตลอดการเล่น', 'Frame Counter ใน Game Loop'],
          ['Memory Footprint', '≤ 200 MB RAM', 'Python tracemalloc'],
          ['Frame Drop', '≤ ร้อยละ 5 ของเฟรมทั้งหมด', 'Delta Time Histogram'],
          ['Startup Time', '≤ 8 วินาทีบน HDD', 'time.perf_counter()'],
          ['Database Write', '≤ 50 ms ต่อ Session Save', 'SQLite Timer'],
          ['Biome Transitions', 'ครบ 4 Biome ที่ 0, 100, 250, 450 ม.', 'Unit Test'],
        ],
        [2800, 3800, 2426]
      ),
      blank(),
      h(2, '6.2 ขอบเขตการทำงานของระบบ (Functional Scope)'),
      p('โมดูลที่ 1 — Core Gameplay Engine:', { bold: true }),
      p('จัดการ Game Loop ที่ 60 FPS, Isometric Rendering, Input Handling (Keyboard + Touch), Camera Interpolation'),
      p('โมดูลที่ 2 — Procedural World Generation:', { bold: true }),
      p('สร้างเส้นทางแบบ Zigzag Infinite ด้วย Diamond-Fork Algorithm, Dynamic Difficulty Scaling, Object Pool สำหรับ Obstacle และ Gem'),
      p('โมดูลที่ 3 — Biome & Narrative System:', { bold: true }),
      p('จัดการการเปลี่ยน Biome ตามระยะทาง, Texture Switching, Atmosphere Overlay, Climate Fact Display'),
      p('โมดูลที่ 4 — Pursuit System (Chaser):', { bold: true }),
      p('ChaserBlock ที่ไล่ตามผู้เล่นตาม Path Array ด้วยความเร็วที่ Scale ตามระยะทาง'),
      p('โมดูลที่ 5 — Data & Economy:', { bold: true }),
      p('SQLite Database สำหรับ Leaderboard, Gem Economy, Skin Unlock System'),
      h(2, '6.3 ขอบเขตที่ไม่รวมอยู่ในโครงการ (Out of Scope)'),
      bullet('ระบบ Multiplayer หรือ Online Leaderboard'),
      bullet('การแปลเป็นภาษาอื่นนอกจากภาษาไทยและภาษาอังกฤษ'),
      bullet('การ Port ไปยังแพลตฟอร์ม Mobile (iOS/Android) ในเวอร์ชันปัจจุบัน'),
      bullet('ระบบ In-App Purchase หรือ Monetization'),

      new Paragraph({ children: [new PageBreak()] }),

      // ══════════════════════════════════════
      // 7. รายละเอียดการพัฒนา
      // ══════════════════════════════════════
      h(1, '7. รายละเอียดของการพัฒนา (Development Details)'),

      // === ADDITION 2: Source Code architecture paragraph at start of Section 7 ===
      p('Source Code ปัจจุบันประกอบด้วยไฟล์ Python จำนวน 28 ไฟล์ (ไม่นับ __init__.py) แบ่งเป็น 4 Layer ได้แก่ Infrastructure Layer (core/ 6 ไฟล์), Domain Layer (game/ 12 ไฟล์), Screen Layer (screens/ 7 ไฟล์), UI Component Layer (ui/ 2 ไฟล์) และ Entry Point (main.py) ระบบที่เป็นหัวใจ ได้แก่ PCG (grid.py), Quiz Event (quiz_manager.py), ChaserBlock (chaser.py), Object Pool (pool.py) และ Climate Report (learning_path.py) มีอยู่ในโค้ดจริงและทำงานได้ในเวอร์ชันที่ส่งแข่งขัน นวัตกรรมหลักคือการบูรณาการ Quiz เข้ากับ Penalty Mechanic โดยตรง กล่าวคือหากตอบผิด ChaserBlock ได้รับ Speed Boost Multiplier β=1.1 เป็นเวลา 30 ก้าว สร้างแรงจูงใจในการเรียนรู้ผ่านกลไกของเกม (Intrinsic Motivation)'),

      h(2, '7.1 เนื้อเรื่องและการออกแบบเชิงบรรยาย (Narrative Design)'),
      h(3, 'บริบทของโลกเกม'),
      p('ปี ค.ศ. 2087 อุณหภูมิเฉลี่ยโลกสูงขึ้น 2.4 องศาเซลเซียสจากยุคก่อนอุตสาหกรรม แผ่นน้ำแข็งในกรีนแลนด์และแอนตาร์กติกาสลายตัวจนระดับน้ำทะเลสูงขึ้น 0.6 เมตร ถิ่นที่อยู่อาศัยของเพนกวินลดลงเหลือเศษเสี้ยวของพื้นที่เดิม ผู้เล่นสวมบทบาทเพนกวินที่ต้องวิ่งข้ามแผ่นน้ำแข็งที่กำลังพังทลาย ระยะทางที่วิ่งได้ทำหน้าที่เป็น "ดัชนีตระหนักรู้" (Awareness Index) สะท้อนระดับความเข้าใจเรื่องสภาพภูมิอากาศของผู้เล่น'),

      h(3, 'การออกแบบ Biome เป็นเรื่องเล่า'),
      blank(),
      makeTable(
        ['Biome', 'ระยะทาง', 'สภาพแวดล้อม', 'ข้อความเชิงสิ่งแวดล้อม'],
        [
          ['❄ Arctic Ice', '0–249 ม.', 'น้ำแข็งขาวบริสุทธิ์ รอยร้าวเริ่มปรากฏ', 'จุดเริ่มต้นของการสูญเสีย'],
          ['🌵 Drought Zone', '250–549 ม.', 'ดินแห้งแตกระแหง สีทรายส้ม', 'น้ำหายไป ความแห้งแล้งเข้าครอบงำ'],
          ['🌊 Flood Surge', '550–899 ม.', 'กระเบื้องน้ำแข็งจมใต้น้ำสีน้ำเงินเข้ม', 'ระดับน้ำทะเลสูงขึ้น เมืองจมหาย'],
          ['🔥 Wildfire', '900+ ม.', 'เถ้าถ่านสีเทาดำ รอยร้าวเรืองแสงส้ม', 'ไฟไหม้ป่าที่ดับไม่ได้'],
        ],
        [1800, 1400, 3000, 2826]
      ),
      blank(),

      // SCREEN 1: Main Menu
      h(3, 'ฉากที่ 1 — Main Menu'),
      p('ออกแบบในโทน Arctic Dark Navy พร้อม Tagline "Every step counts. The ice won\'t wait." ปุ่มนำทางทั้งหมดใช้ Canvas-drawn RoundedRectangle แทน PNG เพื่อลดขนาดไฟล์และเพิ่มความเสถียร'),
      blank(),
      img('assets/report_figures/ui_menu.png', 590, 384, 'Main Menu'),
      caption('รูปที่ 1  หน้า Main Menu — โทน Arctic Dark Navy ออกแบบด้วย Kivy Canvas'),

      // SCREEN 2: Gameplay
      h(3, 'ฉากที่ 2 — Gameplay'),
      p('หัวใจของประสบการณ์ ผู้เล่นบังคับเพนกวินบนตารางไอโซเมตริกที่สร้างขึ้นแบบ Procedural ไม่มีจุดสิ้นสุด พื้นด้านหลังจะพังทลายหากยืนนิ่งเกิน 2 วินาที Chaser Block สีแดงไล่ตามมาจากด้านหลัง และ Biome เปลี่ยนไปทุกๆ ระยะทางที่กำหนด'),
      blank(),
      img('assets/report_figures/ui_gameplay.png', 590, 384, 'Gameplay'),
      caption('รูปที่ 2  หน้า Gameplay — Isometric Grid พร้อม HUD แสดง Awareness Index และ Gem'),

      // SCREEN 3: Game Over
      h(3, 'ฉากที่ 3 — Game Over'),
      p('แสดง "AWARENESS INDEX: X M" พร้อม Climate Fact ที่คัดเลือกให้ตรงกับ Biome สุดท้าย และ Input Field สำหรับบันทึกชื่อลง Leaderboard การแสดง Climate Fact ณ จุดนี้สร้าง Contextual Learning ที่มีประสิทธิภาพสูงตามหลักการ Situated Cognition'),
      blank(),
      img('assets/report_figures/ui_gameover.png', 590, 384, 'Game Over'),
      caption('รูปที่ 3  หน้า Game Over — แสดง Awareness Index และ Climate Fact ตาม Biome สุดท้าย'),

      // SCREEN 4: Quiz Popup
      h(3, 'ฉากที่ 4 — Quiz Popup (Active Learning Event)'),
      p('ระบบ Quiz Event ปรากฏขึ้นระหว่างเกมทุก 50–100 เมตร แสดงคำถามความรู้ด้านสิ่งแวดล้อมพร้อมตัวเลือก 4 ข้อ หากตอบถูกจะได้รับ Gem Bonus หากตอบผิด Chaser จะได้รับ Speed Boost Multiplier β=1.1 เป็นเวลา 30 ก้าว กลไกนี้สร้างแรงจูงใจในการเรียนรู้ตามหลัก Testing Effect (Roediger & Butler, 2011) โดยตรง'),
      blank(),
      img('assets/report_figures/ui_quiz_popup.png', 590, 384, 'Quiz Popup'),
      caption('รูปที่ 4  หน้า Quiz Popup — Active Learning Event ที่แทรกระหว่างการเล่นทุก 50–100 เมตร'),

      // === ADDITION 3: Scene 5 — Climate Report (Learning Progress Dashboard) ===
      h(3, 'ฉากที่ 5 — Climate Report (Learning Progress Dashboard)'),
      p('หน้า Climate Report (learning_path.py) ทำหน้าที่เป็น Learning Dashboard ส่วนตัวของผู้เล่น มีองค์ประกอบที่ implement จริงในโค้ดดังนี้: (1) BiomeCard แสดง Animated Progress Bar ต่อ Biome พร้อมเปอร์เซ็นต์ความแม่นยำ (Accuracy %) คำนวณจากข้อมูล SQLite ที่ดึงมาผ่าน DatabaseManager.get_quiz_stats() (2) FactsPopupWidget แสดง Climate Fact ทั้ง 5 ข้อของแต่ละ Biome ที่มาจาก QUESTIONS Bank ใน quiz_manager.py เปิดได้เมื่อกดปุ่ม View Facts บน BiomeCard แต่ละอัน (3) Global Score Label แสดงคะแนนรวมทั้ง 4 Biome และเปอร์เซ็นต์ความสำเร็จ (4) MASTER Badge ที่ pulse animation เมื่อผู้เล่นตอบถูกครบ 5/5 ข้อใน Biome ใด Biome หนึ่ง และ (5) ปุ่ม Reset Progress พร้อม Confirm Dialog เพื่อล้างข้อมูลและเริ่มการเรียนรู้ใหม่'),
      p('ข้อมูลทั้งหมดบันทึกลง SQLite ผ่าน method save_quiz_answer() และดึงกลับมาด้วย get_quiz_stats() (database.py) ทำให้ Quiz Progress คงอยู่ข้ามเซสชัน ระบบนี้แยกแยะโครงการออกจากเกม Endless Runner ทั่วไป กล่าวคือ The Great Melt ไม่ได้เป็นเพียงเกมที่มีเนื้อหาวิชาการแทรก แต่มีระบบติดตามผลการเรียนรู้ที่วัดผลได้จริงและเชื่อมกับ Penalty Mechanic ของเกมโดยตรง'),
      blank(),
      makeTable(
        ['องค์ประกอบใน Code', 'ไฟล์ / Method', 'สิ่งที่แสดงต่อผู้เล่น'],
        [
          ['BiomeCard + Progress Bar', 'learning_path.py: class BiomeCard', 'ข้อถูก/ทั้งหมด + Accuracy % ต่อ Biome'],
          ['FactsPopupWidget', 'learning_path.py: class FactsPopupWidget', 'Climate Fact 5 ข้อต่อ Biome (ภาษาไทย/อังกฤษ)'],
          ['Global Score Label', 'learning_path.py: _load_stats()', 'คะแนนรวม X/20 + เปอร์เซ็นต์'],
          ['Persistent SQLite', 'database.py: save_quiz_answer / get_quiz_stats', 'ข้อมูลคงอยู่ข้ามเซสชัน'],
        ],
        [2600, 3200, 3226]
      ),
      blank(),

      new Paragraph({ children: [new PageBreak()] }),

      // ══════════════════════════════════════
      // 7.2 อัลกอริทึม
      // ══════════════════════════════════════
      h(2, '7.2 เทคนิคและอัลกอริทึมที่ใช้'),

      // Algorithm 1
      h(3, 'อัลกอริทึมที่ 1 — Isometric Perspective Projection'),
      p('ระบบแสดงผลแปลงพิกัดตาราง 2 มิติ (c, r) ซึ่ง c คือ Column และ r คือ Row ไปเป็นพิกัดหน้าจอ (Sx, Sy) ผ่านสมการ Isometric Projection มาตรฐาน (McShaffry & Graham, 2013):'),
      p('  Sx = (c − r) × Wtile/2       Sy = (c + r) × Htile/2', { extra: { spacing: { before: 60, after: 60 } } }),
      p('โดยที่ W_tile = 130 pixels และ H_tile = 65 pixels ตามอัตราส่วน 2:1 มาตรฐาน Isometric การเรียงลำดับ Z-order ตาม Painter\'s Algorithm ใช้ค่า Depth Key: Z(c,r) = c + r Tile ที่มีค่า Z สูงกว่าถูกวาดก่อน โดยการเรียงลำดับใช้ list.sort() ซึ่งมีความซับซ้อน O(n log n)'),
      blank(),
      img('assets/report_figures/fig_isometric_grid.png', 590, 390, 'Isometric Grid Projection'),
      caption('รูปที่ 6  การแปลงพิกัดตาราง (c, r) ไปเป็นพิกัดหน้าจอด้วย Isometric Projection — W_tile=130, H_tile=65 และตัวอย่างการคำนวณที่ Tile (2,1)'),

      // Algorithm 2
      h(3, 'อัลกอริทึมที่ 2 — Camera Interpolation (Exponential Smoothing)'),
      p('ระบบใช้ Linear Interpolation แบบ Recursive สมมูลกับ Exponential Smoothing ตามที่ Shiffman (2012) อธิบาย:'),
      p('  cam(t+1) = cam(t) + α × (target(t) − cam(t))  โดยที่ α = 0.15 (CAMERA_LERP)', { extra: { spacing: { before: 60, after: 60 } } }),
      p('ที่ t=20 เฟรม กล้องจะเหลือระยะห่างจาก Target เพียง 3.9% ของระยะห่างเริ่มต้น กล่าวคือภายใน 0.33 วินาทีที่ 60 FPS กล้องจะตามทันตัวละครในระดับที่ไม่รบกวนการรับรู้ของผู้เล่น'),

      // Algorithm 3
      h(3, 'อัลกอริทึมที่ 3 — Procedural Content Generation แบบ Constraint-based'),
      p('เส้นทางเกมสร้างขึ้นแบบ Infinite โดยสลับระหว่างสองทิศทาง DIRA=(1,0) และ DIRB=(0,1) ตามหลัก Constraint-based PCG (Shaker, Togelius & Nelson, 2016) ความยาวของแต่ละ Segment:'),
      p('  L_seg = randint(5+e, 12+e)    เมื่อ e = min(6, ⌊d/100⌋)', { extra: { spacing: { before: 60, after: 60 } } }),
      p('Diamond Fork Algorithm สุ่มด้วยความน่าจะเป็น P_fork=0.30 เมื่อจำนวน Segment ≥ 2 สร้างทางแยกรูปเพชรที่มีเส้นทางตรง (4 Tile) และเส้นทางอ้อม โดยเส้นทางอ้อมมี Gem Spawn Rate สูงถึงร้อยละ 60 เพื่อจูงใจให้ผู้เล่นเลือกเส้นทางที่ท้าทายกว่า'),
      blank(),
      img('assets/report_figures/fig_pcg_path.png', 590, 305, 'PCG Path Zigzag Diamond Fork'),
      caption('รูปที่ 7  ภาพรวมเส้นทาง PCG แบบ Zigzag + Diamond Fork: แสดง Path tile, Fork tile, Prop ประเภทต่างๆ ตำแหน่ง Player (P) และ Chaser (C)'),
      blank(),
      img('assets/report_figures/fig_pcg_segment.png', 590, 322, 'PCG Segment Length'),
      caption('รูปที่ 8  การกระจายความยาว Segment (L_seg) ตามระยะทาง d — ช่วงตรงยาวขึ้นเมื่อเข้าสู่ Biome ระดับสูง สร้างความตึงเครียดที่เพิ่มขึ้นตามระยะทาง'),

      // Algorithm 4
      h(3, 'อัลกอริทึมที่ 4 — Prop-String Obstacle System'),
      p('ระบบอุปสรรคใช้ Prop-String ต่อ Tile แทนการสร้าง Object ทุกครั้ง ลดการทำงานของ Garbage Collector ตามหลักการ Flyweight Pattern (Gamma et al., 1994)'),
      blank(),
      makeTable(
        ['Prop', 'พฤติกรรม'],
        [
          ['ice1', 'เหยียบ 1 ครั้งแล้วหาย'],
          ['ice2', 'เหยียบ → ลดเป็น ice1'],
          ['ice3', 'เหยียบ → ลดเป็น ice2'],
          ['force', 'เก็บได้ → Gold Buff 5 วินาที (ทำลาย ice ทันที)'],
          ['trap', 'กับดักที่เปิด/ปิดสลับกัน'],
        ],
        [2000, 7026]
      ),
      blank(),
      makeTable(
        ['Zone', 'ระยะทาง', 'ice1', 'ice2', 'ice3', 'force', 'trap'],
        [
          ['Arctic Ice', '0–79 ม.', '70%', '—', '—', '30%', '—'],
          ['Drought', '80–249 ม.', '40%', '30%', '—', '30%', '—'],
          ['Flood', '250–499 ม.', '25%', '25%', '18%', '16%', '16%'],
          ['Wildfire', '500+ ม.', '15%', '20%', '20%', '17%', '28%'],
        ],
        [1900, 1500, 1000, 1000, 1000, 1000, 1626]
      ),
      blank(),
      img('assets/report_figures/fig_prop_distribution.png', 590, 291, 'Prop Distribution by Zone'),
      caption('รูปที่ 9  การกระจายตัวของ Prop แต่ละประเภทตาม Zone แสดงการเพิ่มขึ้นของ trap และ ice3 ตามความลึกของ Biome'),

      // Algorithm 5
      h(3, 'อัลกอริทึมที่ 5 — Dynamic Difficulty Scaling (Obstacle Density)'),
      p('ความน่าจะเป็นในการสร้าง Obstacle แต่ละ Tile เป็น Step Function ของระยะทาง ตามแนวทาง Dynamic Difficulty Adjustment (Hunicke & Chapman, 2004):'),
      blank(),
      makeTable(
        ['ระยะทาง', 'Obstacle/Tile', 'Gem บน Free Tile', 'Gem Effective Rate'],
        [
          ['0 ม.', '15%', '50%', '42.5%'],
          ['100 ม.', '45%', '40%', '22.0%'],
          ['250 ม.', '58%', '32%', '13.4%'],
          ['500+ ม.', '68%', '32%', '10.2%'],
        ],
        [2300, 2300, 2300, 2126]
      ),
      blank(),

      // Algorithm 6
      h(3, 'อัลกอริทึมที่ 6 — Chaser Pursuit System'),
      p('ChaserBlock ไล่ตามผู้เล่นตาม Path Array ด้วยความเร็ว:'),
      p('  Δt_chaser(d) = max(0.28, 0.80 − d × 0.0013)  วินาทีต่อก้าว', { extra: { spacing: { before: 60, after: 60 } } }),
      p('ChaserBlock เริ่มเคลื่อนไหวเมื่อผู้เล่นถึง Path Index ที่ 20 โดยเริ่มต้นห่างจากผู้เล่น 14 Tile หากผู้เล่นตอบคำถาม Quiz ผิด ระบบเพิ่มความเร็ว Chaser ชั่วคราวผ่าน Speed Boost Multiplier β=1.1 เป็นเวลา 30 ก้าว'),
      blank(),
      makeTable(
        ['ระยะทาง', 'Δt_chaser', 'ความถี่ขยับ'],
        [
          ['0 ม.', '0.80 วิ/ก้าว', '1.25 ก้าว/วิ'],
          ['100 ม.', '0.67 วิ/ก้าว', '1.49 ก้าว/วิ'],
          ['300 ม.', '0.41 วิ/ก้าว', '2.44 ก้าว/วิ'],
          ['400+ ม.', '0.28 วิ/ก้าว', '3.57 ก้าว/วิ (สูงสุด)'],
        ],
        [2500, 3500, 3026]
      ),
      blank(),
      img('assets/report_figures/fig_chaser_speed.png', 590, 321, 'Chaser Speed Curve'),
      caption('รูปที่ 10  กราฟ Chaser Pursuit Speed Curve — Δt_chaser(d) = max(0.28, 0.80−d×0.0013) โดยแบ่ง Biome Zone ด้วยพื้นหลังสี ความเร็วสูงสุดถึง Limit ที่ระยะทาง 400 ม.'),

      // Algorithm 7
      h(3, 'อัลกอริทึมที่ 7 — Object Pooling Pattern'),
      p('ระบบจัดการออบเจกต์ด้วย Object Pool ตามรูปแบบที่ Nystrom (2014) เสนอ โดยวัตถุอย่าง Gem ถูกสร้างไว้ล่วงหน้าใน Pools.gems และนำมาใช้ซ้ำโดยเรียก reset() แทนการสร้างใหม่ทุกครั้ง ลดภาระ Garbage Collector ใน Real-time Game Loop อัตราส่วนการใช้งาน Pool: U_pool = N_active / N_total สอดคล้องกับแนวทาง Green Software Engineering (Pihkola et al., 2018)'),

      // Algorithm 8
      h(3, 'อัลกอริทึมที่ 8 — Grid-based Collision Detection O(1)'),
      p('ระบบตรวจสอบการชนใช้โครงสร้างข้อมูล Hash Set และ Hash Map ของ Python (Sedgewick & Wayne, 2011):'),
      bullet('path_set : Set[(col, row)] → ตรวจสอบว่ายืนบนพื้นหรือไม่'),
      bullet('obstacles : Dict[(col, row) → prop] → ตรวจสอบ Obstacle'),
      bullet('gems : Dict[(col, row) → Gem] → ตรวจสอบ Gem'),
      bullet('path_index_map : Dict[(col,row) → int] → แปลงตำแหน่งเป็น Path Index'),
      p('การตรวจสอบแต่ละครั้งมีความซับซ้อน O(1) Average Case เนื่องจาก Python dict และ set ใช้โครงสร้าง Hash Table ภายใน ทำให้เวลาตรวจสอบคงที่ไม่เปลี่ยนแปลงตามขนาดข้อมูล'),

      new Paragraph({ children: [new PageBreak()] }),

      // ══════════════════════════════════════
      // 7.3 เครื่องมือ + Architecture
      // ══════════════════════════════════════
      h(2, '7.3 เครื่องมือที่ใช้ในการพัฒนา'),
      blank(),
      makeTable(
        ['เครื่องมือ', 'เวอร์ชัน', 'บทบาท'],
        [
          ['Python', '3.12', 'Primary Language'],
          ['Kivy', '2.3.1', 'Cross-platform GUI + OpenGL ES 2.0'],
          ['Pillow', '10.x', 'Procedural Asset Generation'],
          ['SQLite', '3.x (built-in)', 'Local Data Persistence'],
          ['Visual Studio Code', '1.89+', 'IDE + Linting (Pylance)'],
          ['Git', '2.x', 'Version Control'],
          ['virtualenv', '—', 'Dependency Isolation'],
        ],
        [2500, 2000, 4526]
      ),
      blank(),

      // === ADDITION 4: Green IT Software Footprint heading + table + paragraph ===
      h(3, 'น้ำหนักซอฟต์แวร์และสถาปัตยกรรม Green IT (Software Footprint)'),
      p('ขนาดโปรแกรมวัดจากระบบไฟล์จริง (Source Code + Assets รวม) มีดังนี้'),
      blank(),
      makeTable(
        ['ส่วนประกอบ', 'ขนาดจริง (วัดจาก filesystem)', 'หมายเหตุ'],
        [
          ['Assets (ภาพ, เสียง, font)', '5.5 MB', 'สร้างด้วย Pillow — ลิขสิทธิ์ทีมพัฒนา 100%'],
          ['Source Code (28 ไฟล์ .py + style.kv)', '0.8 MB', 'Logic ครบ 4 Layer + 1 Entry Point'],
          ['รวมโปรแกรมทั้งหมด', '6.3 MB', 'เล็กกว่า Storage Requirement 100 MB ถึง 15 เท่า'],
        ],
        [2800, 3200, 3026]
      ),
      blank(),
      p('การเลือกสถาปัตยกรรมตามหลัก Green IT มีผลโดยตรงต่อ Footprint 3 ประการ: (1) Procedural Asset Generation ด้วย Python Pillow ทำให้ไม่จำเป็นต้องใช้ภาพ Raster ความละเอียดสูงจากภายนอก (2) Object Pool สำหรับ Gem กำหนด initial_size=10 และ max_size=200 (pool.py) ป้องกัน Python Garbage Collector ทำงานใน Real-time Game Loop และ (3) O(1) Collision Detection ผ่าน Python dict และ set (grid.py) ทำให้ไม่มี CPU Overhead จาก Linear Search แม้แผนที่จะยาวไม่สิ้นสุด ค่า TARGET_FPS = 60 กำหนดใน config.py เป็นข้อจำกัดบน เพื่อให้ GPU ทำงานพอดีไม่เกินความจำเป็น'),
      blank(),

      h(3, 'สถาปัตยกรรมซอฟต์แวร์ตาม Separation of Concerns'),
      p('โครงการออกแบบตามหลัก Separation of Concerns (Dijkstra, 1982) แบ่งเป็น 4 Layer:'),
      p('Layer 1 — Presentation Layer (style.kv, screens/):', { bold: true }),
      p('จัดการ UI ด้วย KV Language แยกการออกแบบหน้าตาออกจาก Logic ตาม MVC Pattern'),
      p('Layer 2 — Application Layer (screens/gameplay.py):', { bold: true }),
      p('จัดการ Screen Transitions, Game Loop ผ่าน Clock.schedule_interval ที่ 60 FPS, Input Handling'),
      p('Layer 3 — Domain Layer (game/):', { bold: true }),
      p('ประกอบด้วย GridManager, Penguin, ChaserBlock, BiomeManager, ObstacleFactory เป็น Pure Python ไม่ Import Kivy ทำให้ทดสอบได้โดยไม่ต้องเปิด GUI'),
      p('Layer 4 — Infrastructure Layer (core/):', { bold: true }),
      p('DatabaseManager, AudioManager, StateManager ล้วนใช้ Singleton Pattern (Gamma et al., 1994) เพื่อให้มี Instance เดียวตลอด Lifecycle ป้องกัน Duplicate Resource Loading'),
      blank(),
      img('docs/architecture_diagram.png', 590, 276, 'System Architecture'),
      caption('รูปที่ 11  System Architecture ของ The Great Melt แสดง 4 Layer ตามหลัก Separation of Concerns และความสัมพันธ์ระหว่างโมดูลหลัก'),
      blank(),
      p('การออกแบบ Asset ด้วย Procedural Generation: Asset กราฟิกทั้งหมดสร้างด้วย Python Pillow ผ่านสคริปต์ scripts/generate_assets.py ทำให้ลิขสิทธิ์ทุกชิ้นเป็นของทีมพัฒนา ขนาดไฟล์รวมต่ำกว่า 5 เมกะไบต์ สอดคล้องกับเป้าหมาย Green IT'),

      new Paragraph({ children: [new PageBreak()] }),

      // ══════════════════════════════════════
      // 7.4 Software Specification
      // ══════════════════════════════════════
      h(2, '7.4 รายละเอียดโปรแกรมที่จะพัฒนา (Software Specification)'),
      h(3, 'Input Specification'),
      blank(),
      makeTable(
        ['Channel', 'Input', 'Action'],
        [
          ['Keyboard', 'Arrow Left / Right', 'ขยับเพนกวิน'],
          ['Touch', 'Left Zone / Right Zone', 'ขยับเพนกวิน'],
          ['Keyboard', 'Escape / P', 'หยุดเกมชั่วคราว'],
          ['Any', 'แตะบนเมนูหยุด', 'Resume / Restart / Home'],
        ],
        [2000, 3500, 3526]
      ),
      blank(),
      h(3, 'Functional Specification'),
      bullet('Procedural path generation แบบ Infinite ผ่าน Diamond-Fork Algorithm'),
      bullet('Dynamic Biome switching ตามค่า Awareness Index'),
      bullet('Quiz Event popup ทุก 50–100 เมตร พร้อม Reward/Penalty system'),
      bullet('ChaserBlock pursuit system พร้อม Speed scaling'),
      bullet('Falling tile system ที่พื้นพังทลายเมื่อผู้เล่นหยุดนิ่งเกิน 2 วินาที'),
      bullet('Gem economy system เชื่อมกับ Skin unlock'),
      bullet('Climate Report screen แสดง Quiz progress แยกตาม Biome'),
      bullet('รองรับสองภาษา ไทยและอังกฤษ ผ่านระบบ i18n'),
      blank(),
      h(3, 'โครงสร้างของซอฟต์แวร์ (Design) — Entity-Relationship Diagram'),
      p('ระบบฐานข้อมูล SQLite ประกอบด้วย 5 ตาราง: players, sessions, scores, player_skins และ quiz_progress มีความสัมพันธ์แบบ One-to-Many ระหว่างผู้เล่นกับเซสชันการเล่น รองรับการบันทึก Quiz Progress แยกตาม Biome เพื่อแสดงผลใน Climate Report Screen'),
      blank(),
      img('assets/report_figures/fig_er_diagram.png', 590, 343, 'ER Diagram SQLite'),
      caption('รูปที่ 12  Entity-Relationship Diagram ของ SQLite Database Schema แสดงความสัมพันธ์ระหว่าง 5 ตาราง: players, sessions, scores, player_skins, quiz_progress'),
      blank(),
      h(3, 'Minimum System Requirements'),
      blank(),
      makeTable(
        ['Component', 'Requirement'],
        [
          ['OS', 'Windows 10+ / macOS 12+'],
          ['CPU', 'Dual-core 1.8 GHz'],
          ['RAM', '4 GB'],
          ['GPU', 'OpenGL ES 2.0 compatible'],
          ['Storage', '100 MB'],
          ['Internet', 'ไม่จำเป็น (Fully Offline)'],
        ],
        [3000, 6026]
      ),
      blank(),

      // ══════════════════════════════════════
      // 7.5 ขอบเขตและข้อจำกัด
      // ══════════════════════════════════════
      h(2, '7.5 ขอบเขตและข้อจำกัดของโปรแกรมที่พัฒนา'),
      p('ขอบเขตที่ไม่ครอบคลุม:', { bold: true }),
      bullet('ระบบ Multiplayer และ Online Leaderboard ข้ามเครือข่าย'),
      bullet('การ Port ไปยังแพลตฟอร์ม Mobile (iOS/Android) ในเวอร์ชันปัจจุบัน'),
      bullet('การรองรับภาษาอื่นนอกจากภาษาไทยและภาษาอังกฤษ'),
      blank(),
      p('ข้อจำกัดทางเทคนิค:', { bold: true }),
      p('Kivy Framework ใช้ OpenGL ES 2.0 ซึ่งบน macOS เวอร์ชัน 14 (Sonoma) ขึ้นไปต้องกำหนดค่า KIVY_GL_BACKEND=angle ผ่านตัวแปรสภาพแวดล้อมเพื่อให้แสดงผลได้อย่างถูกต้อง ฟอนต์ภาษาไทย Thonburi ใช้งานได้เฉพาะบน macOS เท่านั้น บน Windows ต้องแทนที่ด้วยฟอนต์ TrueType ภาษาไทยที่ติดตั้งในระบบ เช่น Sarabun'),
      blank(),
      p('ข้อจำกัดด้านเนื้อหา:', { bold: true }),
      p('ชุดคำถาม Quiz ในปัจจุบันมีทั้งสิ้น 20 ข้อ แบ่งเป็น 5 ข้อต่อ Biome เมื่อผู้เล่นตอบครบทุกข้อใน Biome ใด ระบบจะหยุดส่ง Quiz Event สำหรับ Biome นั้นจนกว่าจะเริ่มเกมใหม่'),

      new Paragraph({ children: [new PageBreak()] }),

      // ══════════════════════════════════════
      // บรรณานุกรม
      // ══════════════════════════════════════
      h(1, 'บรรณานุกรม'),
      p('Bloom, B. S., Engelhart, M. D., Furst, E. J., Hill, W. H., & Krathwohl, D. R. (1956). Taxonomy of educational objectives: Handbook I: Cognitive domain. David McKay Company.'),
      p('Brown, J. S., Collins, A., & Duguid, P. (1989). Situated cognition and the culture of learning. Educational Researcher, 18(1), 32–42.'),
      p('Freeman, S., et al. (2014). Active learning increases student performance in science, engineering, and mathematics. PNAS, 111(23), 8410–8415. https://doi.org/10.1073/pnas.1319030111'),
      p('Gamma, E., Helm, R., Johnson, R., & Vlissides, J. (1994). Design patterns: Elements of reusable object-oriented software. Addison-Wesley.'),
      p('Germanwatch. (2021). Global Climate Risk Index 2021. https://www.germanwatch.org/en/19777'),
      p('Hunicke, R., & Chapman, V. (2004). AI for dynamic difficulty adjustment in games. AAAI Workshop on Challenges in Game AI, 91–96.'),
      p('IPCC. (2023). AR6 Synthesis Report: Climate Change 2023. https://www.ipcc.ch/report/ar6/syr/'),
      p('Jenouvrier, S., et al. (2020). The Paris Agreement objectives will likely halt future declines of emperor penguins. Global Change Biology, 26(3), 1170–1184.'),
      p('Lüthi, D., et al. (2008). High-resolution carbon dioxide concentration record. Nature, 453(7193), 379–382.'),
      p('Mayer, R. E. (2014). Computer games for learning: An evidence-based approach. MIT Press.'),
      p('McShaffry, M., & Graham, D. (2013). Game coding complete (4th ed.). Course Technology PTR.'),
      p('Murugesan, S. (2008). Harnessing green IT: Principles and practices. IT Professional, 10(1), 24–33.'),
      p('NSIDC. (2023). Arctic Sea Ice News and Analysis. https://nsidc.org/arcticseaicenews/'),
      p('Nystrom, R. (2014). Game programming patterns. http://gameprogrammingpatterns.com/'),
      p('OECD. (2023). PISA 2022 Results (Volume I): The State of Learning and Equity in Education. OECD Publishing. https://doi.org/10.1787/53f23881-en'),
      p('Pihkola, H., et al. (2018). Evaluating the energy consumption of mobile data transfer. Sustainability, 10(7), 2494.'),
      p('Roediger, H. L., & Butler, A. C. (2011). The critical role of retrieval practice. Trends in Cognitive Sciences, 15(1), 20–27.'),
      p('Sedgewick, R., & Wayne, K. (2011). Algorithms (4th ed.). Addison-Wesley.'),
      p('Shaker, N., Togelius, J., & Nelson, M. J. (2016). Procedural content generation in games. Springer.'),
      p('Shiffman, D. (2012). The nature of code. Self-published. https://natureofcode.com/'),
      p('Trope, Y., & Liberman, N. (2010). Construal-level theory of psychological distance. Psychological Review, 117(2), 440–463.'),
      p('United Nations. (2015). Transforming our world: The 2030 Agenda for Sustainable Development. https://sdgs.un.org/2030agenda'),
      p('van der Linden, S. (2015). The social-psychological determinants of climate change risk perceptions. Journal of Environmental Psychology, 41, 112–124.'),
      p('WMO. (2023). State of the Global Climate 2022. https://wmo.int/'),
      p('Yale Program on Climate Change Communication. (2022). Climate change in the American mind. https://climatecommunication.yale.edu/'),
      p('กระทรวงศึกษาธิการ. (2566). สถิติการศึกษาของประเทศไทย ปีการศึกษา 2565. สำนักงานเลขาธิการสภาการศึกษา.'),

      new Paragraph({ children: [new PageBreak()] }),

      // ══════════════════════════════════════
      // ประวัติผู้พัฒนา
      // ══════════════════════════════════════
      h(1, 'ประวัติและผลงานด้านวิชาการของผู้พัฒนาโครงการ'),
      p('นายอภิชาติ จะหย่อ', { bold: true }),
      p('ระดับการศึกษา: นักศึกษาระดับปริญญาตรี คณะวิศวกรรมศาสตร์ สาขาวิศวกรรมคอมพิวเตอร์ มหาวิทยาลัยสงขลานครินทร์'),
      p('ผลงาน: —'),
    ],
  }],
});

Packer.toBuffer(doc).then(buffer => {
  const outPath = `${BASE}/NSC2026_Report_TheGreatMelt.docx`;
  fs.writeFileSync(outPath, buffer);
  console.log('SUCCESS:', outPath);
  console.log('Size:', (buffer.length / 1024).toFixed(1), 'KB');
}).catch(err => {
  console.error('ERROR:', err.message);
  process.exit(1);
});
