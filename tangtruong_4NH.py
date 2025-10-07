import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="💰 Thưởng 4NH - BHX", layout="wide")
st.title("💰 Thưởng Tăng trưởng 4 Ngành hàng Chọn - BHX")

# === Đọc dữ liệu ===
dthumodel = pd.read_excel("dthu.xlsx")
mapping_st = pd.read_excel("mapping_st.xlsx")
mapping_4nh = pd.read_excel("mapping_4NH.xlsx")
target_4nh = pd.read_excel("target4NH.xlsx")

# === Chuẩn hóa tên cột ===
for df in [dthumodel, mapping_st, mapping_4nh, target_4nh]:
    df.columns = df.columns.str.strip()

# === Merge dữ liệu với mapping siêu thị ===
merged = pd.merge(dthumodel, mapping_st, on="Mã siêu thị", how="left")

# === Kiểm tra & merge ngành hàng ===
if "Ngành hàng BHX" in merged.columns and "Ngành hàng BHX" in mapping_4nh.columns:
    merged = pd.merge(merged, mapping_4nh, on="Ngành hàng BHX", how="left")
elif "Ngành hàng" in merged.columns and "Ngành hàng BHX" in mapping_4nh.columns:
    merged = pd.merge(
        merged,
        mapping_4nh,
        left_on="Ngành hàng",
        right_on="Ngành hàng BHX",
        how="left"
    )

# === Nếu thiếu cột % chia sẻ → thêm mặc định 0 ===
if "% chia sẻ" not in merged.columns:
    merged["% chia sẻ"] = 0

# === Tính tổng doanh thu ===
if "Doanh thu" in merged.columns:
    # Xác định cột ngành hàng hợp lệ
    if "NH" in merged.columns:
        nh_col = "NH"
    elif "NH chọn" in merged.columns:
        nh_col = "NH chọn"
    elif "Ngành hàng BHX" in merged.columns:
        nh_col = "Ngành hàng BHX"
    else:
        st.error("⚠️ Không tìm thấy cột ngành hàng trong dữ liệu (NH / NH chọn / Ngành hàng BHX)")
        st.stop()

    tong = (
        merged.groupby(["mst", "tenst", "% chia sẻ", nh_col], as_index=False)["Doanh thu"]
        .sum()
        .copy()
    )

    # === Tính Doanh thu dự kiến ===
    today = datetime.datetime.now().day
    tong["Doanh thu dự kiến"] = tong["Doanh thu"] / max(today - 1, 1) * 31

    # === Merge thêm Target và % chia sẻ từ target_4nh ===
    if {"mst", "NH chọn"}.issubset(target_4nh.columns):
        tong = pd.merge(
            tong,
            target_4nh[["mst", "NH chọn", "target", "% chia sẻ"]],
            on=["mst", "NH chọn"],
            how="left",
            suffixes=("", "_target")
        )
        # Nếu % chia sẻ từ target tồn tại, ưu tiên dùng
        tong["% chia sẻ"] = tong["% chia sẻ_target"].combine_first(tong["% chia sẻ"])
        tong.drop(columns=["% chia sẻ_target"], inplace=True)
    else:
        st.warning("⚠️ File target4NH.xlsx thiếu cột 'mst' hoặc 'NH chọn'")

    # === Lọc target khác 0 ===
    tong = tong[tong["target"].fillna(0) != 0]

    # === Xử lý % chia sẻ ===
    tong["% chia sẻ"] = (
        tong["% chia sẻ"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", ".", regex=False)
        .replace("", "0")
        .astype(float)
 
    )

    # === Tính thêm cột Doanh thu tăng thêm & Thưởng ===
    tong["Doanh thu tăng thêm"] = tong["Doanh thu dự kiến"] - tong["target"]
    tong["Thưởng"] = tong["Doanh thu tăng thêm"] * tong["% chia sẻ"]

    # === Giá trị âm => 0 ===
    cols_fix = ["Doanh thu dự kiến", "Doanh thu tăng thêm", "Thưởng"]
    tong[cols_fix] = tong[cols_fix].clip(lower=0)

    # === Selectbox chọn siêu thị ===
    st.subheader("🛒 Chọn siêu thị để xem chi tiết")
    list_st = ["Tất cả"] + sorted(tong["tenst"].dropna().unique().tolist())
    selected_st = st.selectbox("Chọn siêu thị:", list_st, index=0)

    if selected_st != "Tất cả":
        tong = tong[tong["tenst"] == selected_st]

    # === Chọn cột hiển thị ===
    tong = tong[[
        "mst", "tenst", "NH chọn", "% chia sẻ",
        "Doanh thu", "Doanh thu dự kiến", "target",
        "Doanh thu tăng thêm", "Thưởng"
    ]]

    # === Đổi tên cột theo ý muốn ===
    tong.rename(columns={
        "mst": "Mã ST",
        "tenst": "Tên Siêu Thị",
        "NH chọn": "Ngành Hàng",
        "% chia sẻ": "% Chia Sẻ",
        "Doanh thu": "Doanh Thu",
        "Doanh thu dự kiến": "Doanh thu dự kiến",
        "target": "Target",
        "Doanh thu tăng thêm": "Tăng Thêm",
        "Thưởng": "Thưởng"
    }, inplace=True)

    # === Thêm hàng Tổng cộng ===
    total_row = pd.DataFrame({
        "Mã ST": ["Tổng"],
        "Tên Siêu Thị": [""],
        "Ngành Hàng": [""],
        "% Chia Sẻ": [tong["% Chia Sẻ"].mean()],
        "Doanh Thu": [tong["Doanh Thu"].sum()],
        "Doanh thu dự kiến": [tong["Doanh thu dự kiến"].sum()],
        "Target": [tong["Target"].sum()],
        "Tăng Thêm": [tong["Tăng Thêm"].sum()],
        "Thưởng": [tong["Thưởng"].sum()],
    })
    tong = pd.concat([tong, total_row], ignore_index=True)

    # === Highlight dòng Tổng ===
    def highlight_total(row):
        if row["Mã ST"] == "Tổng":
            return ["background-color: #F8F8FF; font-weight: bold;"] * len(row)
        else:
            return [""] * len(row)

    # === Hiển thị bảng ===
    st.subheader("📊 Doanh thu Dự kiến, Target & Thưởng dự kiến")
    st.dataframe(
        tong.style
        .apply(highlight_total, axis=1)
        .format({
            "% Chia Sẻ": "{:.1%}",
            "Doanh Thu": "{:,.0f}",
            "Doanh thu dự kiến": "{:,.0f}",
            "Target": "{:,.0f}",
            "Tăng Thêm": "{:,.0f}",
            "Thưởng": "{:,.0f}"
        })
        .set_table_styles([
            {'selector': 'th', 'props': [('font-weight', 'bold')]}
        ]),
        use_container_width=True
    )
else:
    st.error("⚠️ Không tìm thấy cột 'Doanh thu' trong file dthumodel.xlsx")
