import streamlit as st
import pandas as pd
import datetime

# =========================
# ⚙️ CẤU HÌNH CHUNG
# =========================
today = datetime.datetime.now().day
st.set_page_config(page_title="💰 Báo Cáo Thưởng BHX", layout="wide")
st.title("💰 Báo Cáo Thưởng 4 Ngành hàng & Hiệu quả Fresh - BHX")
st.markdown(
    f"<h5 style='text-align:center; color:gray;'>(Dữ liệu cập nhật đến ngày {today-1}/10)</h5>",
    unsafe_allow_html=True
)

# =========================
# 📘 ĐỌC FILE DỮ LIỆU
# =========================
try:
    dthumodel = pd.read_excel("dthu.xlsx")
    mapping_st = pd.read_excel("mapping_st.xlsx")
    mapping_4nh = pd.read_excel("mapping_4NH.xlsx")
    target_4nh = pd.read_excel("target4NH.xlsx")
    thuong_fresh = pd.read_excel("thuong_fresh.xlsx", sheet_name="Siêu thị")
except Exception as e:
    st.error(f"⚠️ Lỗi khi đọc file: {e}")
    st.stop()

# --- Chuẩn hóa cột ---
for df in [dthumodel, mapping_st, mapping_4nh, target_4nh]:
    for col in ["Mã siêu thị", "mst"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r"\.0$", "", regex=True)
    df.columns = df.columns.str.strip()

# =========================
# 🏷️ LẤY DANH SÁCH SIÊU THỊ
# =========================
if "tenst" in mapping_st.columns:
    ten_sieuthi_list = sorted(mapping_st["tenst"].dropna().unique().tolist())
else:
    ten_sieuthi_list = sorted(dthumodel["Tên siêu thị"].dropna().unique().tolist())

chon_st = st.selectbox("🛒 Chọn Siêu thị:", ["-- Tất cả --"] + ten_sieuthi_list)

# =========================
# 1️⃣ BẢNG THƯỞNG 4 NGÀNH HÀNG CHỌN
# =========================
st.subheader("📊 Thưởng Tăng trưởng 4 Ngành hàng Chọn")

merged = pd.merge(dthumodel, mapping_st, on="Mã siêu thị", how="left")

if "Ngành hàng BHX" in merged.columns and "Ngành hàng BHX" in mapping_4nh.columns:
    merged = pd.merge(merged, mapping_4nh, on="Ngành hàng BHX", how="left")
elif "Ngành hàng" in merged.columns and "Ngành hàng BHX" in mapping_4nh.columns:
    merged = pd.merge(
        merged, mapping_4nh,
        left_on="Ngành hàng",
        right_on="Ngành hàng BHX",
        how="left"
    )

if "% chia sẻ" not in merged.columns:
    merged["% chia sẻ"] = 0

if "Doanh thu" not in merged.columns:
    st.error("⚠️ Không tìm thấy cột 'Doanh thu' trong file dthu.xlsx")
else:
    nh_col = next((c for c in ["NH", "NH chọn", "Ngành hàng BHX"] if c in merged.columns), None)
    if not nh_col:
        st.error("⚠️ Không tìm thấy cột ngành hàng trong dữ liệu")
        st.stop()

    tong = (
        merged.groupby(["mst", "tenst", "% chia sẻ", nh_col], as_index=False)["Doanh thu"]
        .sum()
    )
    tong["Doanh thu dự kiến"] = tong["Doanh thu"] / max(today - 1, 1) * 31

    # Merge Target
    if {"mst", "NH chọn"}.issubset(target_4nh.columns):
        tong = pd.merge(
            tong,
            target_4nh[["mst", "NH chọn", "target", "% chia sẻ"]],
            on=["mst", "NH chọn"],
            how="left",
            suffixes=("", "_target")
        )
        tong["% chia sẻ"] = tong["% chia sẻ_target"].combine_first(tong["% chia sẻ"])
        tong.drop(columns=["% chia sẻ_target"], inplace=True)
    else:
        st.warning("⚠️ File target4NH.xlsx thiếu cột 'mst' hoặc 'NH chọn'")

    tong = tong[tong["target"].fillna(0) != 0]
    tong["% chia sẻ"] = (
        tong["% chia sẻ"].astype(str)
        .str.replace("%", "").str.replace(",", ".").replace("", "0").astype(float)
    )

    tong["Doanh thu tăng thêm"] = tong["Doanh thu dự kiến"] - tong["target"]
    tong["Thưởng"] = tong["Doanh thu tăng thêm"] * tong["% chia sẻ"]
    cols_fix = ["Doanh thu dự kiến", "Doanh thu tăng thêm", "Thưởng"]
    tong[cols_fix] = tong[cols_fix].clip(lower=0)

    # Lọc siêu thị
    if chon_st != "-- Tất cả --":
        tong = tong[tong["tenst"] == chon_st]

    tong = tong.rename(columns={
        "mst": "Mã ST",
        "tenst": "Tên Siêu Thị",
        "NH chọn": "Ngành Hàng",
        "% chia sẻ": "% Chia Sẻ",
        "Doanh thu": "Doanh Thu",
        "Doanh thu dự kiến": "Doanh thu Dự kiến",
        "target": "Target",
        "Doanh thu tăng thêm": "Tăng Thêm",
        "Thưởng": "Thưởng"
    })

    total_row = pd.DataFrame({
        "Mã ST": ["Tổng"],
        "Tên Siêu Thị": [""],
        "Ngành Hàng": [""],
        "% Chia Sẻ": [tong["% Chia Sẻ"].mean()],
        "Doanh Thu": [tong["Doanh Thu"].sum()],
        "Doanh thu Dự kiến": [tong["Doanh thu Dự kiến"].sum()],
        "Target": [tong["Target"].sum()],
        "Tăng Thêm": [tong["Tăng Thêm"].sum()],
        "Thưởng": [tong["Thưởng"].sum()],
    })
    tong = pd.concat([tong, total_row], ignore_index=True)

    def highlight_total(row):
        return ["background-color: #F8F8FF; font-weight: bold;" if row["Mã ST"] == "Tổng" else ""] * len(row)

    st.dataframe(
        tong.style
        .apply(highlight_total, axis=1)
        .format({
            "% Chia Sẻ": "{:.1%}",
            "Doanh Thu": "{:,.0f}",
            "Doanh thu Dự kiến": "{:,.0f}",
            "Target": "{:,.0f}",
            "Tăng Thêm": "{:,.0f}",
            "Thưởng": "{:,.0f}"
        }),
        use_container_width=True
    )

# =========================
# 2️⃣ BẢNG THƯỞNG HIỆU QUẢ FRESH
# =========================
st.subheader("🥬 Thưởng Hiệu quả Fresh")

# Kiểm tra dữ liệu fresh
if "Tên siêu thị" not in thuong_fresh.columns:
    st.error("⚠️ Không tìm thấy cột 'Tên siêu thị' trong sheet 'Siêu thị'")
else:
    if chon_st != "-- Tất cả --":
        df_fresh = thuong_fresh[thuong_fresh["Tên siêu thị"] == chon_st]
    else:
        df_fresh = thuong_fresh.copy()

    # Hiển thị cột 1→13
    df_fresh = df_fresh.iloc[:, 1:14]

    # Cột Còn thiếu
    if all(c in df_fresh.columns for c in ["Doanh thu", "Giá vốn cơ bản"]):
        df_fresh["Còn thiếu"] = df_fresh["Doanh thu"] - df_fresh["Giá vốn cơ bản"]

    # Format số
    df_fmt = df_fresh.copy()
    for c in df_fmt.select_dtypes(include=["number"]).columns:
        df_fmt[c] = df_fmt[c].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else "")

    def highlight_negative(val):
        try:
            v = float(str(val).replace(",", ""))
            return "color: red;" if v < 0 else ""
        except:
            return ""

    def highlight_last(x):
        df_style = pd.DataFrame("", index=x.index, columns=x.columns)
        if len(x) > 0:
            df_style.loc[x.index[-1], :] = "font-weight: bold; background-color: #f6f6f6;"
        return df_style

    styled_fresh = df_fmt.style.applymap(highlight_negative).apply(highlight_last, axis=None)
    st.dataframe(styled_fresh, use_container_width=True)
