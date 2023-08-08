from utils.utils import read_csv_to_pandas, write_df_to_parquet, timestamp_to_date_and_time, add_to_dates_set
import pandas as pd
import numpy as np
import logging


logger = logging.getLogger('MyLogger')
logger.setLevel(logging.INFO)


def transform_design(file, source_bucket, target_bucket, timestamp):
    try:
        design_table = read_csv_to_pandas(file, source_bucket)
        dim_design_table = design_table.loc[:, ['design_id', 'design_name', 'file_location', 'file_name']]
        write_df_to_parquet(dim_design_table, 'dim_design', target_bucket, timestamp)
        logger.info(f'dim_design.parquet successfully created in {target_bucket}')
    except Exception as e:
        logger.error('ERROR: transform_design')
        raise e


def transform_payment_type(file, source_bucket, target_bucket, timestamp):
    try:
        payment_type_table = read_csv_to_pandas(file, source_bucket)
        dim_payment_type_table = payment_type_table.loc[:, ['payment_type_id', 'payment_type_name']]
        write_df_to_parquet(dim_payment_type_table, 'dim_payment_type', target_bucket, timestamp)
        logger.info(f'dim_payment_type.parquet successfully created in {target_bucket}')
    except Exception as e:
        logger.error('ERROR: transform_payment_type')
        raise e


def transform_location(file, source_bucket, target_bucket, timestamp):
    try:
        address_table = read_csv_to_pandas(file, source_bucket)
        dim_address_table = address_table.loc[:, ['address_id', 'address_line_1', 'address_line_2', 'district', 'city', 'postal_code', 'country', 'phone']]
        dim_address_table.rename(columns={'address_id': 'location_id'}, inplace=True)
        write_df_to_parquet(dim_address_table, 'dim_location', target_bucket, timestamp)
        logger.info(f'dim_location.parquet successfully created in {target_bucket}')
    except Exception as e:
        logger.error('ERROR: transform_location')
        raise e


def transform_transaction(file, source_bucket, target_bucket, timestamp):
    try:
        transaction_table = read_csv_to_pandas(file, source_bucket)
        dim_transaction_table = transaction_table.loc[:, ['transaction_id', 'transaction_type', 'sales_order_id', 'purchase_order_id']]
        write_df_to_parquet(dim_transaction_table, 'dim_transaction', target_bucket, timestamp)
        logger.info(f'dim_transaction.parquet successfully created in {target_bucket}')
    except Exception as e:
        logger.error('ERROR: transform_transaction')
        raise e


def transform_staff(file1, file2, source_bucket, target_bucket, timestamp):
    try:
        staff_table = read_csv_to_pandas(file1, source_bucket)
        department_table = read_csv_to_pandas(file2, source_bucket)
        joined_staff_department_table = staff_table.join(department_table.set_index('department_id'), on='department_id', lsuffix="staff", rsuffix='department')
        dim_staff_table = joined_staff_department_table.loc[:, ['staff_id', 'first_name', 'last_name', 'department_name', 'location', 'email_address']]
        write_df_to_parquet(dim_staff_table, 'dim_staff', target_bucket, timestamp)
        logger.info(f'dim_staff.parquet successfully created in {target_bucket}')
    except Exception as e:
        logger.error('ERROR: transform_staff')
        raise e


def transform_currency(file, source_bucket, target_bucket, timestamp):
    try:
        currency_table = read_csv_to_pandas(file, source_bucket)
        dim_currency_table = currency_table.loc[:, ['currency_id', 'currency_code']]
        conditions = [(dim_currency_table['currency_code'] == 'EUR'), (dim_currency_table['currency_code'] == 'GBP'), (dim_currency_table['currency_code'] == 'USD')]
        values = ['Euro', 'British Pound', 'US Dollar']
        dim_currency_table['currency_name'] = np.select(conditions, values)
        write_df_to_parquet(dim_currency_table, 'dim_currency', target_bucket, timestamp)
        logger.info(f'dim_currency.parquet successfully created in {target_bucket}')
    except Exception as e:
        logger.error('ERROR: transform_currency')
        raise e


def transform_counterparty(file1, file2, source_bucket, target_bucket, timestamp):
    try:
        counterparty_table = read_csv_to_pandas(file1, source_bucket)
        address_table_for_counterparty = read_csv_to_pandas(file2, source_bucket)
        joined_counterparty_address_table = counterparty_table.join(address_table_for_counterparty.set_index('address_id'), on='legal_address_id', lsuffix='counterparty', rsuffix='address')
        dim_counterparty = joined_counterparty_address_table.loc[:, ['counterparty_id', 'counterparty_legal_name', 'address_line_1', 'address_line_2', 'district', 'city', 'postal_code', 'country', 'phone']]
        columns_to_rename = ['address_line_1', 'address_line_2', 'district', 'city', 'postal_code', 'country']
        dim_counterparty.rename(columns={col: 'counterparty_legal_'+col for col in dim_counterparty.columns if col in columns_to_rename}, inplace=True)
        dim_counterparty.rename(columns={'phone': 'counterparty_legal_phone_number'}, inplace=True)
        write_df_to_parquet(dim_counterparty, 'dim_counterparty', target_bucket, timestamp)
        logger.info(f'dim_counterparty.parquet successfully created in {target_bucket}')
    except Exception as e:
        logger.error('ERROR: transform_counterparty')
        raise e


def transform_sales_order(file, source_bucket, target_bucket, dates_for_dim_date, timestamp):
    try:
        sales_order_table = read_csv_to_pandas(file, source_bucket)
        
        sales_order_table = timestamp_to_date_and_time(sales_order_table)

        sales_order_table.rename(columns={'staff_id': 'sales_staff_id'}, inplace=True)
        fact_sales_order = sales_order_table.loc[:, ['sales_order_id', 'created_date', 'created_time', 'last_updated_date', 'last_updated_time', 'sales_staff_id', 'counterparty_id', 'units_sold', 'unit_price', 'currency_id', 'design_id', 'agreed_payment_date', 'agreed_delivery_date', 'agreed_delivery_location_id']]
        write_df_to_parquet(fact_sales_order, 'fact_sales_order', target_bucket, timestamp)
        logger.info(f'fact_sales_order.parquet successfully created in {target_bucket}')

        date_cols_to_add = [fact_sales_order['created_date'], fact_sales_order['last_updated_date'],fact_sales_order['agreed_payment_date'], fact_sales_order['agreed_delivery_date']]
        add_to_dates_set(dates_for_dim_date, date_cols_to_add)
    except Exception as e:
        logger.error('ERROR: transform_sales_order')
        raise e


def transform_purchase_order(file, source_bucket, target_bucket, dates_for_dim_date, timestamp):
    try:
        purchase_order_table = read_csv_to_pandas(file, source_bucket)

        purchase_order_table = timestamp_to_date_and_time(purchase_order_table)

        fact_purchase_order = purchase_order_table.loc[:, ['purchase_order_id', 'created_date', 'created_time', 'last_updated_date', 'last_updated_time', 'staff_id', 'counterparty_id', 'item_code', 'item_quantity', 'item_unit_price', 'currency_id', 'agreed_delivery_date', 'agreed_payment_date', 'agreed_delivery_location_id']]
        write_df_to_parquet(fact_purchase_order, 'fact_purchase_order', target_bucket, timestamp)
        logger.info(f'fact_purchase_order.parquet successfully created in {target_bucket}')

        date_cols_to_add = [fact_purchase_order['created_date'], fact_purchase_order['last_updated_date'], fact_purchase_order['agreed_delivery_date'], fact_purchase_order['agreed_payment_date']]
        add_to_dates_set(dates_for_dim_date, date_cols_to_add)
    except Exception as e:
        logger.error('ERROR: transform_purchase_order')
        raise e


def transform_payment(file, source_bucket, target_bucket, dates_for_dim_date, timestamp):
    try:
        payment_table = read_csv_to_pandas(file, source_bucket)

        payment_table = timestamp_to_date_and_time(payment_table)

        fact_payment_table = payment_table.loc[:, ['payment_id', 'created_date', 'created_time', 'last_updated_date', 'last_updated_time', 'transaction_id', 'counterparty_id', 'payment_amount', 'currency_id', 'payment_type_id', 'paid', 'payment_date']]
        write_df_to_parquet(fact_payment_table, 'fact_payment', target_bucket, timestamp)
        logger.info(f'fact_payment.parquet successfully created in {target_bucket}')

        date_cols_to_add = [fact_payment_table['created_date'], fact_payment_table['last_updated_date'], fact_payment_table['payment_date']]
        add_to_dates_set(dates_for_dim_date, date_cols_to_add)
    except Exception as e:
        logger.error('ERROR: transform_payment')
        raise e


def create_date(dates_for_dim_date, target_bucket, timestamp):
    try:
        dates = {'date_id': sorted(list(dates_for_dim_date))}
        dim_date = pd.DataFrame(data=dates)
        dim_date['year'] = pd.DatetimeIndex(dim_date['date_id']).year
        dim_date['month'] = pd.DatetimeIndex(dim_date['date_id']).month
        dim_date['day'] = pd.DatetimeIndex(dim_date['date_id']).day
        dim_date['day_of_week'] = pd.DatetimeIndex(dim_date['date_id']).dayofweek
        dim_date['day_name'] = pd.DatetimeIndex(dim_date['date_id']).day_name()
        dim_date['month_name'] = pd.DatetimeIndex(dim_date['date_id']).month_name()
        dim_date['quarter'] = pd.DatetimeIndex(dim_date['date_id']).quarter
        write_df_to_parquet(dim_date, 'dim_date', target_bucket, timestamp)
        logger.info(f'dim_date.parquet successfully created in {target_bucket}')
    except Exception as e:
        logger.error('ERROR: create_date')
        raise e
    
    # run in terminal to view pq table --> parquet-tools show s3://processed-va-052023/dim_date.parquet