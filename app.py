import streamlit as st
import pandas as pd
import numpy as np


# ==================================================
# ページ設定
# ==================================================

st.set_page_config(
    page_title="店舗発注サポート",
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="auto"
)


# ==================================================
# 基本設定
# ==================================================

SALES_DAYS = 7
LEAD_TIME = 3

EVENT_OPTIONS = [
    "通常時",
    "チラシ掲載時",
    "お盆シーズン",
    "年末年始シーズン"
]


# ==================================================
# Session State
# ==================================================

if "new_products" not in st.session_state:
    st.session_state.new_products = []


# ==================================================
# タイトル
# ==================================================

st.title("📦 店舗発注サポート")

st.caption(
    "販売実績・在庫・イベント状況から、"
    "発注推奨数を自動計算します。"
)


# ==================================================
# サイドバー
# ==================================================

with st.sidebar:

    st.header("⚙️ 発注設定")

    # --------------------------------------------------
    # イベント設定
    # --------------------------------------------------

    st.subheader("📅 シーズン・イベント")

    selected_event = st.selectbox(
        "現在のシーズン",
        EVENT_OPTIONS
    )

    st.caption("イベントごとの倍率")

    normal_multiplier = st.number_input(
        "通常時",
        min_value=0.1,
        max_value=10.0,
        value=1.0,
        step=0.1
    )

    flyer_multiplier = st.number_input(
        "チラシ掲載時",
        min_value=0.1,
        max_value=10.0,
        value=1.5,
        step=0.1
    )

    obon_multiplier = st.number_input(
        "お盆シーズン",
        min_value=0.1,
        max_value=10.0,
        value=2.0,
        step=0.1
    )

    year_end_multiplier = st.number_input(
        "年末年始シーズン",
        min_value=0.1,
        max_value=10.0,
        value=2.5,
        step=0.1
    )

    event_multipliers = {
        "通常時": normal_multiplier,
        "チラシ掲載時": flyer_multiplier,
        "お盆シーズン": obon_multiplier,
        "年末年始シーズン": year_end_multiplier
    }

    selected_multiplier = event_multipliers[
        selected_event
    ]

    st.info(
        f"現在：{selected_event}\n\n"
        f"倍率：{selected_multiplier:.1f}倍"
    )

    st.divider()

    # --------------------------------------------------
    # 新商品追加
    # --------------------------------------------------

    st.subheader("🆕 新商品の追加")

    with st.form(
        "new_product_form",
        clear_on_submit=True
    ):

        new_product_code = st.text_input(
            "商品コード",
            placeholder="例：490000000001"
        )

        new_product_name = st.text_input(
            "商品名",
            placeholder="例：季節限定チューハイ"
        )

        new_category = st.text_input(
            "カテゴリー",
            placeholder="例：チューハイ"
        )

        new_stock = st.number_input(
            "現在の在庫数",
            min_value=0,
            value=0,
            step=1
        )

        new_average_sales = st.number_input(
            "予測1日平均販売数",
            min_value=0.0,
            value=1.0,
            step=0.1
        )

        add_button = st.form_submit_button(
            "➕ 新商品を追加",
            use_container_width=True
        )

        if add_button:

            code = new_product_code.strip()
            name = new_product_name.strip()
            category = new_category.strip()

            if not code:

                st.error(
                    "商品コードを入力してください。"
                )

            elif not name:

                st.error(
                    "商品名を入力してください。"
                )

            elif not category:

                st.error(
                    "カテゴリーを入力してください。"
                )

            else:

                existing_codes = {
                    str(product["商品コード"])
                    for product
                    in st.session_state.new_products
                }

                if code in existing_codes:

                    st.error(
                        "同じ商品コードが"
                        "すでに登録されています。"
                    )

                else:

                    st.session_state.new_products.append(
                        {
                            "商品コード": code,
                            "商品名": name,
                            "カテゴリー": category,
                            "在庫数": int(new_stock),
                            "1日平均販売数":
                                float(new_average_sales),
                            "データ区分": "新商品"
                        }
                    )

                    st.success(
                        f"「{name}」を追加しました。"
                    )

    # --------------------------------------------------
    # 新商品一覧
    # --------------------------------------------------

    if st.session_state.new_products:

        st.divider()

        st.caption(
            f"追加済み："
            f"{len(st.session_state.new_products)}商品"
        )

        with st.expander(
            "追加済み新商品を見る"
        ):

            for product in (
                st.session_state.new_products
            ):

                st.write(
                    f"**{product['商品名']}**"
                )

                st.caption(
                    f"{product['カテゴリー']} ｜ "
                    f"在庫 {product['在庫数']} ｜ "
                    f"予測 "
                    f"{product['1日平均販売数']}個/日"
                )

        if st.button(
            "🗑️ 新商品をすべて削除",
            use_container_width=True
        ):

            st.session_state.new_products = []
            st.rerun()


# ==================================================
# CSVアップロード
# ==================================================

st.subheader("① データを読み込む")

sales_file = st.file_uploader(
    "販売データ CSV",
    type=["csv"]
)

stock_file = st.file_uploader(
    "在庫データ CSV",
    type=["csv"]
)


# ==================================================
# CSVが揃っていない場合
# ==================================================

if sales_file is None or stock_file is None:

    st.info(
        "販売データと在庫データの"
        "2つをアップロードしてください。"
    )

    st.markdown(
        """
**販売CSVに必要な列**

`日付 / 商品コード / 商品名 / カテゴリー / 販売数`

**在庫CSVに必要な列**

`商品コード / 商品名 / カテゴリー / 在庫数`
"""
    )

    st.stop()


# ==================================================
# データ処理開始
# ==================================================

try:

    sales_df = pd.read_csv(
        sales_file,
        dtype={"商品コード": str}
    )

    stock_df = pd.read_csv(
        stock_file,
        dtype={"商品コード": str}
    )


    # ==================================================
    # 必須列チェック
    # ==================================================

    sales_required = {
        "日付",
        "商品コード",
        "商品名",
        "カテゴリー",
        "販売数"
    }

    stock_required = {
        "商品コード",
        "商品名",
        "カテゴリー",
        "在庫数"
    }

    missing_sales = (
        sales_required
        - set(sales_df.columns)
    )

    missing_stock = (
        stock_required
        - set(stock_df.columns)
    )

    if missing_sales:

        st.error(
            "販売CSVに不足している列："
            + "、".join(missing_sales)
        )

        st.stop()

    if missing_stock:

        st.error(
            "在庫CSVに不足している列："
            + "、".join(missing_stock)
        )

        st.stop()


    # ==================================================
    # データ整理
    # ==================================================

    sales_df["商品コード"] = (
        sales_df["商品コード"]
        .astype(str)
        .str.strip()
    )

    stock_df["商品コード"] = (
        stock_df["商品コード"]
        .astype(str)
        .str.strip()
    )

    sales_df["カテゴリー"] = (
        sales_df["カテゴリー"]
        .fillna("未分類")
        .astype(str)
        .str.strip()
    )

    stock_df["カテゴリー"] = (
        stock_df["カテゴリー"]
        .fillna("未分類")
        .astype(str)
        .str.strip()
    )

    sales_df.loc[
        sales_df["カテゴリー"] == "",
        "カテゴリー"
    ] = "未分類"

    stock_df.loc[
        stock_df["カテゴリー"] == "",
        "カテゴリー"
    ] = "未分類"


    # ==================================================
    # 数値・日付変換
    # ==================================================

    sales_df["日付"] = pd.to_datetime(
        sales_df["日付"],
        errors="coerce"
    )

    sales_df["販売数"] = pd.to_numeric(
        sales_df["販売数"],
        errors="coerce"
    ).fillna(0)

    stock_df["在庫数"] = pd.to_numeric(
        stock_df["在庫数"],
        errors="coerce"
    ).fillna(0)

    sales_df = sales_df.dropna(
        subset=["日付"]
    )

    if sales_df.empty:

        st.error(
            "有効な日付を含む販売データがありません。"
        )

        st.stop()


    # ==================================================
    # 直近7日
    # ==================================================

    latest_date = sales_df[
        "日付"
    ].max()

    start_date = (
        latest_date
        - pd.Timedelta(
            days=SALES_DAYS - 1
        )
    )

    recent_sales = sales_df[
        (
            sales_df["日付"]
            >= start_date
        )
        &
        (
            sales_df["日付"]
            <= latest_date
        )
    ].copy()


    # ==================================================
    # 販売実績集計
    # ==================================================

    sales_summary = (
        recent_sales
        .groupby(
            "商品コード",
            as_index=False
        )["販売数"]
        .sum()
    )

    sales_summary.rename(
        columns={
            "販売数": "直近7日販売数"
        },
        inplace=True
    )

    sales_summary[
        "1日平均販売数"
    ] = (
        sales_summary[
            "直近7日販売数"
        ]
        / SALES_DAYS
    )


    # ==================================================
    # 在庫データと結合
    # ==================================================

    result = pd.merge(
        stock_df,
        sales_summary,
        on="商品コード",
        how="left"
    )

    result["直近7日販売数"] = (
        result["直近7日販売数"]
        .fillna(0)
    )

    result["1日平均販売数"] = (
        result["1日平均販売数"]
        .fillna(0)
    )

    result["データ区分"] = "既存商品"


    # ==================================================
    # 手動追加商品の追加
    # ==================================================

    if st.session_state.new_products:

        new_products_df = pd.DataFrame(
            st.session_state.new_products
        )

        new_products_df[
            "商品コード"
        ] = (
            new_products_df[
                "商品コード"
            ]
            .astype(str)
            .str.strip()
        )

        new_products_df[
            "直近7日販売数"
        ] = 0

        existing_codes = set(
            result["商品コード"]
        )

        duplicate_mask = (
            new_products_df[
                "商品コード"
            ].isin(
                existing_codes
            )
        )

        if duplicate_mask.any():

            st.warning(
                "CSV内の商品コードと"
                "重複する新商品は除外しました。"
            )

        new_products_df = (
            new_products_df[
                ~duplicate_mask
            ]
        )

        new_products_df = (
            new_products_df[
                [
                    "商品コード",
                    "商品名",
                    "カテゴリー",
                    "在庫数",
                    "直近7日販売数",
                    "1日平均販売数",
                    "データ区分"
                ]
            ]
        )

        result = pd.concat(
            [
                result,
                new_products_df
            ],
            ignore_index=True
        )


    # ==================================================
    # イベント補正
    # ==================================================

    result["イベント"] = (
        selected_event
    )

    result["イベント倍率"] = (
        selected_multiplier
    )

    result[
        "イベント補正後の1日予測販売数"
    ] = (
        result["1日平均販売数"]
        * selected_multiplier
    )


    # ==================================================
    # 発注計算
    # ==================================================

    result[
        "リードタイム中必要数"
    ] = (
        result[
            "イベント補正後の1日予測販売数"
        ]
        * LEAD_TIME
    )

    result[
        "最終発注推奨数"
    ] = (
        result[
            "リードタイム中必要数"
        ]
        - result["在庫数"]
    )

    result[
        "最終発注推奨数"
    ] = (
        result[
            "最終発注推奨数"
        ]
        .clip(lower=0)
    )

    result[
        "最終発注推奨数"
    ] = (
        np.ceil(
            result[
                "最終発注推奨数"
            ]
        )
        .astype(int)
    )


    # ==================================================
    # 小数整理
    # ==================================================

    result[
        "1日平均販売数"
    ] = (
        result[
            "1日平均販売数"
        ]
        .round(2)
    )

    result[
        "イベント補正後の1日予測販売数"
    ] = (
        result[
            "イベント補正後の1日予測販売数"
        ]
        .round(2)
    )

    result[
        "リードタイム中必要数"
    ] = (
        result[
            "リードタイム中必要数"
        ]
        .round(2)
    )


    # ==================================================
    # カテゴリー選択
    # ==================================================

    st.divider()

    st.subheader(
        "② 発注対象を確認"
    )

    categories = sorted(
        result["カテゴリー"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_category = st.selectbox(
        "カテゴリー",
        ["すべて"] + categories
    )

    if selected_category == "すべて":

        filtered_result = (
            result.copy()
        )

    else:

        filtered_result = (
            result[
                result["カテゴリー"]
                == selected_category
            ]
            .copy()
        )


    # ==================================================
    # 現在の条件
    # ==================================================

    st.info(
        f"📅 {selected_event}　"
        f"× {selected_multiplier:.1f}倍"
    )

    st.caption(
        f"販売集計："
        f"{start_date.date()} ～ "
        f"{latest_date.date()}"
    )


    # ==================================================
    # スマホ向けサマリー
    # ==================================================

    order_list = (
        filtered_result[
            filtered_result[
                "最終発注推奨数"
            ] > 0
        ]
        .copy()
    )

    total_products = len(
        filtered_result
    )

    order_products = len(
        order_list
    )

    total_order_quantity = int(
        order_list[
            "最終発注推奨数"
        ].sum()
    )


    # 2列までにしてスマホで見やすくする
    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "商品数",
            f"{total_products}"
        )

    with col2:

        st.metric(
            "発注対象",
            f"{order_products}"
        )

    st.metric(
        "📦 総発注推奨数",
        f"{total_order_quantity} 個"
    )


    # ==================================================
    # 発注対象商品
    # ==================================================

    st.subheader(
        "🛒 発注した方がよい商品"
    )

    if order_list.empty:

        st.success(
            "現在の条件では、"
            "発注対象の商品はありません。"
        )

    else:

        # スマホ用のコンパクト表示
        mobile_columns = [
            "商品名",
            "カテゴリー",
            "在庫数",
            "イベント補正後の1日予測販売数",
            "最終発注推奨数"
        ]

        st.dataframe(
            order_list[
                mobile_columns
            ],
            use_container_width=True,
            hide_index=True,
            height=420
        )


    # ==================================================
    # 商品ごとのカード表示
    # ==================================================

    if not order_list.empty:

        with st.expander(
            "📱 商品ごとに詳しく見る"
        ):

            for _, row in (
                order_list.iterrows()
            ):

                st.markdown(
                    f"### {row['商品名']}"
                )

                st.caption(
                    f"{row['カテゴリー']} ｜ "
                    f"商品コード："
                    f"{row['商品コード']}"
                )

                detail_col1, detail_col2 = (
                    st.columns(2)
                )

                with detail_col1:

                    st.metric(
                        "現在庫",
                        f"{int(row['在庫数'])}"
                    )

                with detail_col2:

                    st.metric(
                        "1日予測",
                        f"{row['イベント補正後の1日予測販売数']}"
                    )

                st.metric(
                    "🔥 最終発注推奨",
                    f"{int(row['最終発注推奨数'])} 個"
                )

                st.divider()


    # ==================================================
    # 全商品の詳細
    # ==================================================

    with st.expander(
        "📊 全商品の計算結果を見る"
    ):

        detail_columns = [
            "商品コード",
            "商品名",
            "カテゴリー",
            "データ区分",
            "直近7日販売数",
            "1日平均販売数",
            "イベント倍率",
            "イベント補正後の1日予測販売数",
            "在庫数",
            "リードタイム中必要数",
            "最終発注推奨数"
        ]

        st.dataframe(
            filtered_result[
                detail_columns
            ],
            use_container_width=True,
            hide_index=True
        )


    # ==================================================
    # CSVダウンロード
    # ==================================================

    st.divider()

    st.subheader(
        "③ 発注リストを保存"
    )


    export_columns = [
        "商品コード",
        "商品名",
        "カテゴリー",
        "データ区分",
        "直近7日販売数",
        "1日平均販売数",
        "イベント",
        "イベント倍率",
        "イベント補正後の1日予測販売数",
        "在庫数",
        "リードタイム中必要数",
        "最終発注推奨数"
    ]


    # --------------------------------------------------
    # 発注対象CSV
    # --------------------------------------------------

    order_csv = (
        order_list[
            export_columns
        ]
        .to_csv(
            index=False
        )
        .encode(
            "utf-8-sig"
        )
    )


    st.download_button(
        "🛒 発注リストをCSV保存",
        data=order_csv,
        file_name=(
            f"発注リスト_"
            f"{selected_category}_"
            f"{selected_event}.csv"
        ),
        mime="text/csv",
        use_container_width=True,
        type="primary"
    )


    # --------------------------------------------------
    # 現在表示中CSV
    # --------------------------------------------------

    filtered_csv = (
        filtered_result[
            export_columns
        ]
        .to_csv(
            index=False
        )
        .encode(
            "utf-8-sig"
        )
    )


    st.download_button(
        "📥 現在表示中の商品をCSV保存",
        data=filtered_csv,
        file_name=(
            f"商品データ_"
            f"{selected_category}.csv"
        ),
        mime="text/csv",
        use_container_width=True
    )


    # --------------------------------------------------
    # 全商品CSV
    # --------------------------------------------------

    all_csv = (
        result[
            export_columns
        ]
        .to_csv(
            index=False
        )
        .encode(
            "utf-8-sig"
        )
    )


    st.download_button(
        "📦 全商品データをCSV保存",
        data=all_csv,
        file_name="商品データ_全商品.csv",
        mime="text/csv",
        use_container_width=True
    )


except Exception as e:

    st.error(
        "データ処理中にエラーが発生しました。"
    )

    st.exception(e)
